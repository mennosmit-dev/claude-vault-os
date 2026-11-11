import io
import json
import subprocess
from datetime import date
from pathlib import Path

import pytest
from conftest import ROOT, load

hooks = load("hooks", ROOT / "_system" / "hooks.py")

TODAY = date(2026, 11, 11)


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# --- vault discovery ---------------------------------------------------------


def test_vault_root_prefers_claude_project_dir(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(tmp_path))
    assert hooks.vault_root() == tmp_path.resolve()


def test_vault_root_falls_back_to_script_location(monkeypatch):
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    assert hooks.vault_root() == ROOT


def test_projects_are_folders_with_a_workdoc(vault):
    (vault / "Notes").mkdir()  # no workdoc: not a project
    write(vault / "Beta" / "Workdoc - Beta.md", "")
    assert [p.name for p in hooks.projects(vault)] == ["Alpha", "Beta"]


# --- counting ----------------------------------------------------------------


def test_count_tasks_open_and_late(vault):
    write(
        vault / "Alpha" / "tasks.md",
        "## Doing\n"
        "- [ ] late one  [due:: 2026-11-10]\n"
        "- [ ] due today  [due:: 2026-11-11]\n"
        "  - [ ] indented, no date\n"
        "- [x] finished  [due:: 2026-01-01]\n",
    )
    assert hooks.count_tasks(vault / "Alpha", TODAY) == (3, 1)


def test_count_tasks_without_file(tmp_path):
    assert hooks.count_tasks(tmp_path, TODAY) == (0, 0)


def test_next_step_takes_first_bullet_under_heading(vault):
    write(
        vault / "Alpha" / "session.md",
        "## Last done\n- old\n\n## Next step\n\n- Run the baseline\n- second\n## Other\n- no\n",
    )
    assert hooks.next_step(vault / "Alpha") == "Run the baseline"


def test_next_step_empty_when_missing(vault):
    assert hooks.next_step(vault / "Alpha") == ""


def test_once_fires_once_per_key(tmp_path):
    state = tmp_path / "state"
    assert hooks.once(state, "daystart", "2026-11-11") is True
    assert hooks.once(state, "daystart", "2026-11-11") is False
    assert hooks.once(state, "daystart", "2026-11-12") is True


# --- session start -----------------------------------------------------------


def test_session_start_overview_and_parked(vault):
    write(vault / "Alpha" / "tasks.md", "- [ ] a  [due:: 2026-11-01]\n- [ ] b\n")
    write(vault / "Alpha" / "session.md", "## Open first\nwhere we were\n\n## Next step\n- ship it\n")
    text = hooks.session_start(vault, {"source": "resume"}, TODAY)
    assert "Alpha: 2 open, 1 late. Next: ship it" in text
    assert "PARKED" in text
    assert "DAY START" not in text  # only on a fresh startup


def test_session_start_day_start_only_first_startup(vault):
    write(vault / "Alpha" / "tasks.md", "- [ ] a\n")
    first = hooks.session_start(vault, {"source": "startup"}, TODAY)
    second = hooks.session_start(vault, {"source": "startup"}, TODAY)
    assert "DAY START" in first and "NEW MONTH" in first
    assert "DAY START" not in second and "NEW MONTH" not in second


def test_session_start_no_day_start_without_open_tasks(vault):
    text = hooks.session_start(vault, {"source": "startup"}, TODAY)
    assert "DAY START" not in text


def test_session_start_empty_vault_returns_none(tmp_path):
    assert hooks.session_start(tmp_path, {"source": "resume"}, TODAY) is None


# --- stop: which projects need a session.md update ---------------------------


def jl(*items) -> list[str]:
    return [json.dumps(i) for i in items]


def tool_use(name: str, path: Path) -> dict:
    return {
        "type": "assistant",
        "message": {"content": [{"type": "tool_use", "name": name, "input": {"file_path": str(path)}}]},
    }


def tool_result() -> dict:
    return {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}}


def prompt(text: str) -> dict:
    return {"type": "user", "message": {"content": text}}


def test_edited_this_turn_stops_at_the_last_real_prompt(tmp_path):
    old, new = tmp_path / "old.md", tmp_path / "new.md"
    lines = jl(
        prompt("earlier"),
        tool_use("Write", old),
        prompt("this turn"),
        tool_use("Read", tmp_path / "read.md"),
        tool_result(),
        tool_use("Edit", new),
        tool_result(),
    )
    lines.insert(3, "not json")
    assert hooks.edited_this_turn(lines) == [new.resolve()]


def test_needs_maintenance_ignores_bookkeeping_only_turns(vault):
    a = vault / "Alpha"
    assert hooks.needs_maintenance(vault, [(a / "tasks.md").resolve()]) == []
    assert hooks.needs_maintenance(vault, [(a / "Workdoc - Alpha.md").resolve()]) == []
    assert hooks.needs_maintenance(vault, [(a / "note.md").resolve()]) == ["Alpha"]
    # session.md already updated this turn: nothing to ask
    assert hooks.needs_maintenance(vault, [(a / "note.md").resolve(), (a / "session.md").resolve()]) == []
    # edits outside any project
    assert hooks.needs_maintenance(vault, [(vault / "README.md").resolve()]) == []


def test_stop_blocks_once_with_instructions(vault):
    transcript = write(
        vault / "t.jsonl", "\n".join(jl(prompt("go"), tool_use("Write", vault / "Alpha" / "note.md"))) + "\n"
    )
    decision = hooks.stop(vault, {"transcript_path": str(transcript)}, TODAY)
    assert decision["decision"] == "block"
    assert "Alpha" in decision["reason"] and "2026-11-11" in decision["reason"]
    # second pass of the same Stop event must not loop
    assert hooks.stop(vault, {"transcript_path": str(transcript), "stop_hook_active": True}, TODAY) is None


def test_stop_without_transcript_is_silent(vault):
    assert hooks.stop(vault, {}, TODAY) is None
    assert hooks.stop(vault, {"transcript_path": str(vault / "missing.jsonl")}, TODAY) is None


# --- git ---------------------------------------------------------------------


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True).stdout


@pytest.fixture
def repo(vault):
    git(vault, "init", "-q")
    git(vault, "config", "user.name", "Test")
    git(vault, "config", "user.email", "test@example.invalid")
    git(vault, "config", "commit.gpgsign", "false")
    return vault


def test_commit_only_when_dirty(repo):
    assert hooks.commit(repo, "first") is True
    assert hooks.commit(repo, "nothing changed") is False
    write(repo / "Alpha" / "note.md", "x")
    assert hooks.commit(repo, "second") is True
    assert git(repo, "log", "--format=%s").split() == ["second", "first"]


def test_commit_outside_git_is_noop(vault):
    assert hooks.commit(vault, "msg") is False


def test_push_is_opt_in(repo, monkeypatch):
    git(repo, "remote", "add", "origin", "https://example.invalid/vault.git")
    monkeypatch.delenv("VAULT_AUTOPUSH", raising=False)
    assert hooks.should_push(repo, now=1e10) is False
    monkeypatch.setenv("VAULT_AUTOPUSH", "1")
    assert hooks.should_push(repo, now=1e10) is True


def test_push_throttled_by_stamp(repo, monkeypatch):
    git(repo, "remote", "add", "origin", "https://example.invalid/vault.git")
    monkeypatch.setenv("VAULT_AUTOPUSH", "1")
    stamp = repo / ".git" / "last-push"
    stamp.touch()
    mtime = stamp.stat().st_mtime
    assert hooks.should_push(repo, now=mtime + 60) is False
    assert hooks.should_push(repo, now=mtime + hooks.PUSH_EVERY + 1) is True


def test_push_needs_a_remote(repo, monkeypatch):
    monkeypatch.setenv("VAULT_AUTOPUSH", "1")
    assert hooks.should_push(repo, now=1e10) is False


# --- entry point -------------------------------------------------------------


def test_main_prints_hook_json(vault, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(vault))
    out = io.StringIO()
    hooks.main(["session-start"], io.StringIO('{"source": "resume"}'), out)
    payload = json.loads(out.getvalue())
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "Alpha" in payload["hookSpecificOutput"]["additionalContext"]


def test_main_tolerates_bad_stdin(vault, monkeypatch):
    monkeypatch.setenv("CLAUDE_PROJECT_DIR", str(vault))
    out = io.StringIO()
    hooks.main(["stop"], io.StringIO("not json"), out)
    assert out.getvalue() == ""
