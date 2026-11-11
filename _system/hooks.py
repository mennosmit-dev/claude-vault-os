"""Vault hooks, wired in .claude/settings.json.

    python hooks.py session-start   SessionStart: project overview, parked work, day start, monthly blind spots
    python hooks.py stop            Stop: ask Claude to update session.md, only for projects edited this turn
    python hooks.py backup          Stop: commit; push at most every 30 minutes (opt-in)
    python hooks.py end             SessionEnd: commit and push (opt-in)

Design: scripts do the counting, the model only works when there is something to maintain.
Standard library only, so it runs with `uv run --no-project` and no install step.

Vault root: $CLAUDE_PROJECT_DIR (set by Claude Code), else the folder above _system/.
Push: only when VAULT_AUTOPUSH=1 and a remote exists. Commits always happen in a git repo.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import TextIO

EDIT_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}
BOOKKEEPING = {"session.md", "tasks.md", "decisions.md"}
PUSH_EVERY = 30 * 60
DUE = re.compile(r"\[due:: (\d{4}-\d{2}-\d{2})\]")


def vault_root() -> Path:
    env = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env).resolve() if env else Path(__file__).resolve().parent.parent


def state_dir(vault: Path) -> Path:
    return vault / ".claude" / "state"


def projects(vault: Path) -> list[Path]:
    """A project is a top-level folder with a `Workdoc - <name>.md`."""
    return sorted(p for p in vault.iterdir() if p.is_dir() and any(p.glob("Workdoc - *.md")))


def once(state: Path, name: str, key: str) -> bool:
    """True the first time `key` is seen for `name` (e.g. today's date, this month)."""
    f = state / f"{name}.txt"
    if f.exists() and f.read_text(encoding="utf-8").strip() == key:
        return False
    state.mkdir(parents=True, exist_ok=True)
    f.write_text(key, encoding="utf-8")
    return True


def count_tasks(project: Path, today: date) -> tuple[int, int]:
    """(open, late) from tasks.md. Late = open with a due date before today."""
    f = project / "tasks.md"
    if not f.exists():
        return 0, 0
    open_, late = 0, 0
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("- [ ]"):
            open_ += 1
            m = DUE.search(line)
            if m and m.group(1) < today.isoformat():
                late += 1
    return open_, late


def next_step(project: Path) -> str:
    """First bullet under `## Next step` in session.md."""
    f = project / "session.md"
    if not f.exists():
        return ""
    lines = f.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("## next step"):
            for nxt in lines[i + 1 :]:
                if nxt.startswith("#"):
                    break
                if nxt.strip().startswith("-") and len(nxt.strip()) > 2:
                    return nxt.strip().lstrip("- ").strip()
    return ""


def session_start(vault: Path, inp: dict, today: date) -> str | None:
    """Context injected at session start. None when there is nothing to say."""
    parts, rows = [], []
    total_open = total_late = 0
    for p in projects(vault):
        n_open, n_late = count_tasks(p, today)
        total_open += n_open
        total_late += n_late
        rows.append(f"- {p.name}: {n_open} open, {n_late} late. Next: {next_step(p) or '-'}")
        s = p / "session.md"
        if s.exists() and "## Open first" in s.read_text(encoding="utf-8"):
            parts.append(
                f"PARKED: '{p.name}/session.md' has '## Open first'. Show it as your first answer (skill park)."
            )
    if rows:
        parts.append("VAULT OVERVIEW (do not repeat unless asked):\n" + "\n".join(rows))

    if inp.get("source") == "startup":
        state = state_dir(vault)
        if total_open and once(state, "daystart", today.isoformat()):
            parts.append(
                f"DAY START: first session today, {total_open} open tasks, {total_late} late. "
                "Suggest /chief in one sentence in your first answer. Only run it on yes."
            )
        if once(state, "blindspots", today.strftime("%Y-%m")):
            parts.append("NEW MONTH: mention /blind-spots in one sentence, after the day start.")
    return "\n\n".join(parts) if parts else None


def edited_this_turn(lines: Iterable[str]) -> list[Path]:
    """Files written by edit tools since the last real user prompt (JSONL transcript lines)."""
    paths = []
    for raw in reversed(list(lines)):
        try:
            item = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if not isinstance(item, dict):
            continue
        content = (item.get("message") or {}).get("content")
        if item.get("type") == "user":
            is_tool_result = isinstance(content, list) and any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content
            )
            if not is_tool_result:
                break  # the prompt that started this turn
        if item.get("type") == "assistant" and isinstance(content, list):
            for b in content:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") in EDIT_TOOLS:
                    args = b.get("input") or {}
                    fp = args.get("file_path") or args.get("notebook_path")
                    if fp:
                        paths.append(Path(fp).resolve())
    return paths


def needs_maintenance(vault: Path, edited: list[Path]) -> list[str]:
    """Projects with real edits this turn whose session.md was not updated yet."""
    todo = []
    for p in projects(vault):
        root = p.resolve()
        mine = [e for e in edited if root in e.parents]
        if not mine or (root / "session.md") in mine:
            continue
        if all(e.name in BOOKKEEPING or e.name.startswith("Workdoc - ") for e in mine):
            continue
        todo.append(p.name)
    return todo


def stop(vault: Path, inp: dict, today: date) -> dict | None:
    """Block the stop once and ask for a short bookkeeping turn, if needed."""
    if inp.get("stop_hook_active"):
        return None
    transcript = Path(inp.get("transcript_path") or "")
    if not inp.get("transcript_path") or not transcript.is_file():
        return None
    todo = needs_maintenance(vault, edited_this_turn(transcript.read_text(encoding="utf-8").splitlines()))
    if not todo:
        return None
    d = today.isoformat()
    return {
        "decision": "block",
        "reason": (
            f"Short maintenance, one turn, say nothing about it. For project(s) {', '.join(todo)}: "
            f"(1) session.md: one line under '## Last done' with {d} and what happened; update '## Next step'; "
            "max 15 lines, drop stale lines. "
            f"(2) Workdoc '#### Log': one line '- [{d}] ...' with links. "
            "(3) tasks.md / decisions.md only if this turn produced a task, finished one ([done:: date]) or a decision."
        ),
    }


def git(vault: Path, *args: str, timeout: int = 20) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=vault, capture_output=True, text=True, timeout=timeout)


def commit(vault: Path, msg: str) -> bool:
    if not (vault / ".git").exists() or not git(vault, "status", "--porcelain").stdout.strip():
        return False
    git(vault, "add", "-A")
    return git(vault, "commit", "-q", "-m", msg).returncode == 0


def should_push(vault: Path, now: float) -> bool:
    if os.environ.get("VAULT_AUTOPUSH") != "1" or not git(vault, "remote").stdout.strip():
        return False
    stamp = vault / ".git" / "last-push"
    return not (stamp.exists() and now - stamp.stat().st_mtime < PUSH_EVERY)


def backup(vault: Path) -> None:
    commit(vault, f"Autosave {time.strftime('%Y-%m-%d %H:%M')}")
    if not should_push(vault, time.time()):
        return
    (vault / ".git" / "last-push").touch()
    subprocess.Popen(
        ["git", "push", "-q"],
        cwd=vault,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def end(vault: Path) -> None:
    commit(vault, f"Autosave {time.strftime('%Y-%m-%d %H:%M')} (end)")
    if os.environ.get("VAULT_AUTOPUSH") == "1" and git(vault, "remote").stdout.strip():
        if git(vault, "rev-list", "--count", "@{u}..HEAD").stdout.strip() not in ("", "0"):
            git(vault, "push", "-q", timeout=30)
            (vault / ".git" / "last-push").touch()


def main(argv: list[str], stdin: TextIO, stdout: TextIO) -> None:
    try:
        inp = json.loads(stdin.read() or "{}")
    except json.JSONDecodeError:
        inp = {}
    if not isinstance(inp, dict):
        inp = {}
    vault, today, cmd = vault_root(), date.today(), argv[0]
    if cmd == "session-start":
        text = session_start(vault, inp, today)
        if text:
            out = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": text}}
            stdout.write(json.dumps(out) + "\n")
    elif cmd == "stop":
        decision = stop(vault, inp, today)
        if decision:
            stdout.write(json.dumps(decision) + "\n")
    elif cmd == "backup":
        backup(vault)
    elif cmd == "end":
        end(vault)
    else:
        raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main(sys.argv[1:], sys.stdin, sys.stdout)
