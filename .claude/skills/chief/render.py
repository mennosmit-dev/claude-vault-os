"""Chief of staff for the whole vault: reads tasks.md in every project and does the bookkeeping.

    python render.py planning [--focus ".."] [--week "Project=sentence" ...] [--project X] [--no-open]
        Writes _export/chief-planning.html (deadlines, reminders, project cards, correction field) and
        opens it through a local server (port 8765), so corrections land in .claude/state/chief-corrections.md.
    python render.py serve
        The server itself; planning starts it when needed.
    python render.py cards [--project X]
        Prints the open tasks as JSON for question_round.py (/chief tasks).
    python render.py apply  < answers.json
        Applies the /chief tasks answers to the tasks.md files.

Task line: - [ ] Task  [due:: YYYY-MM-DD]  [owner:: Name]  [prio:: high|medium|low]
Sections: ## Doing, ## This week, ## Next week, ## Backlog, ## Done.
"This week" is the coming work week: Mon to Thu the current week, from Friday the week after.
"Next week" is the work week after that; those tasks move to This week by themselves when that week starts.
Derived, no section: overdue (due < today), today (Doing + due = today),
waiting on others (owner is set and is not VAULT_OWNER).

The model writes only the focus line and the per-project sentences; the rest is deterministic.
Standard library only.
"""

import argparse
import html
import json
import os
import re
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
VAULT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or SCRIPT_DIR.parents[2])  # chief -> skills -> .claude -> vault
TEMPLATE = SCRIPT_DIR / "planning.template.html"
OUTPUT = VAULT / "_export" / "chief-planning.html"
REMINDERS = VAULT / "Reminders.md"  # optional
STATE = VAULT / ".claude" / "state"
CORRECTIONS = STATE / "chief-corrections.md"
CARDS_STATE = STATE / "chief-tasks.json"
WEEK_STATE = STATE / "next-week.json"  # Monday that "Next week" refers to
PORT = 8765
MAX_DEADLINES = 6
COLORS = ["#5b7db1", "#c98a4b", "#6e9e8a", "#9a7bb0", "#c4747a", "#7a9cb8"]
ME = os.environ.get("VAULT_OWNER", "me").strip().lower()  # your name in [owner:: ...]
SECTIONS = ["Doing", "This week", "Next week", "Backlog", "Done"]
# choice -> (section, action)
CHOICES = {
    "today": ("Doing", "due"),
    "this week": ("This week", "week"),
    "next week": ("Next week", "week after"),
    "later": ("Backlog", "no due"),
    "done": ("Done", "done"),
    "drop": (None, "drop"),
}
MONTHS = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_FULL = [
    "",
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]
QUOTES = [  # rotate per day
    "One thing at a time. The rest is safe in the vault.",
    "Done beats perfect.",
    "A steady pace is still a pace.",
    "You don't need everything today, only the next thing.",
    "What you write down, you don't have to remember.",
    "A good question to the right person saves a day of searching.",
    "Starting small is still starting.",
]
DAY_SHORT = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
TASK = re.compile(r"^- \[( |x)\]\s+(.*)$")


def work_week(today):
    """Monday of the coming work week: from Friday on, that is the week after."""
    monday = today - timedelta(days=today.weekday())
    return monday + timedelta(days=7) if today.weekday() >= 4 else monday


def week_deadline(line, monday):
    """Deadline within the work week of monday: a date already in that week stays, otherwise Friday."""
    m = re.search(r"\[due:: (\d{4}-\d{2}-\d{2})\]", line)
    if m and monday.isoformat() <= m.group(1) <= (monday + timedelta(days=4)).isoformat():
        return line
    return set_field(line, "due", (monday + timedelta(days=4)).isoformat())


def period(monday):
    friday = monday + timedelta(days=4)
    return f"Mon {monday.day} {MONTHS[monday.month]} to Fri {friday.day} {MONTHS[friday.month]}"


def options(today):
    week = work_week(today)
    return [
        {"value": "today", "label": "Today", "hint": "to Doing, due today"},
        {
            "value": "this week",
            "label": "This week",
            "hint": f"{period(week)}, due Friday unless already a day that week",
        },
        {
            "value": "next week",
            "label": "Next week",
            "hint": f"{period(week + timedelta(days=7))}, due Friday unless already a day that week",
        },
        {"value": "later", "label": "Later", "hint": "to Backlog, date removed"},
        {"value": "done", "label": "Already done", "hint": "check off"},
        {"value": "drop", "label": "Drop", "hint": "delete the line"},
    ]


def section_index(lines, s):
    """Line after the heading '## s'; if the heading is missing, insert it in the right place."""
    if f"## {s}" not in lines:
        following = SECTIONS[SECTIONS.index(s) + 1 :] + ["Related"]
        spot = next((lines.index(f"## {v}") for v in following if f"## {v}" in lines), len(lines))
        lines[spot:spot] = [f"## {s}", ""]
    return lines.index(f"## {s}") + 1


def roll_over(today):
    """Once the week of 'Next week' has started, move those tasks to This week in every project."""
    try:
        monday = date.fromisoformat(json.loads(WEEK_STATE.read_text(encoding="utf-8"))["monday"])
    except (OSError, ValueError, KeyError):
        return
    if work_week(today) < monday:
        return
    n = 0
    for folder in projects():
        path = folder / "tasks.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        if "## Next week" not in lines:
            continue
        i = lines.index("## Next week") + 1
        j = next((k for k in range(i, len(lines)) if lines[k].startswith("## ")), len(lines))
        moved = [r for r in lines[i:j] if TASK.match(r)]
        if not moved:
            continue
        lines[i:j] = [r for r in lines[i:j] if not TASK.match(r)]
        k = section_index(lines, "This week")
        lines[k:k] = moved
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        n += len(moved)
    WEEK_STATE.unlink()
    if n:
        print(f"rolled over: {n} tasks from Next week to This week", file=sys.stderr)


def projects(filter_=None):
    for folder in sorted(p for p in VAULT.iterdir() if p.is_dir() and not p.name.startswith((".", "_"))):
        if filter_ and filter_.lower() not in folder.name.lower():
            continue
        if (folder / "tasks.md").exists():
            yield folder


def parse(folder):
    tasks, section = [], None
    for nr, line in enumerate((folder / "tasks.md").read_text(encoding="utf-8").splitlines()):
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            section = heading.group(1)
            continue
        m = TASK.match(line)
        if not m:
            continue
        fields = dict(re.findall(r"\[(\w+):: ([^\]]*)\]", m.group(2)))
        title = re.split(r"\s*\[\w+::", m.group(2), maxsplit=1)[0].strip()
        tasks.append(
            {
                "project": folder.name,
                "section": section,
                "done": m.group(1) == "x",
                "title": title,
                "fields": fields,
                "line": line,
                "nr": nr,
            }
        )
    return tasks


def due(t):
    try:
        return date.fromisoformat(t["fields"].get("due", "").strip())
    except ValueError:
        return None


def is_mine(t):
    return t["fields"].get("owner", ME).strip().lower() in ("", ME)


def short(iso):
    try:
        d = date.fromisoformat(iso.strip())
    except (ValueError, AttributeError):
        return ""
    return f"{d.day} {MONTHS[d.month]}"


def li(t, label, cls=""):
    title = t["title"].replace("`", "")
    who = "" if is_mine(t) else f' <span class="who">· {html.escape(t["fields"]["owner"].strip())}</span>'
    task = html.escape(f"{t['project']}: {title}", quote=True)
    return (
        f'<li data-task="{task}" title="{task}"><span class="pill{cls}">{label}</span>'
        f'<span class="t">{html.escape(title)}{who}</span><span class="p">{html.escape(t["project"])}</span></li>'
    )


def day_label(d, today):
    if d < today:
        return short(d.isoformat())
    if d == today:
        return "today"
    return f"{DAY_SHORT[d.weekday()]} {d.day}/{d.month}"


def card(name, tasks, sentence, color, today):
    """One project: the chief's sentence (or the first tasks if missing), plus count and next deadline."""
    mine = [t for t in tasks if not t["done"] and is_mine(t) and t["section"] in ("Doing", "This week")]
    if not sentence:
        sentence = "; ".join(t["title"].replace("`", "") for t in mine[:2]) or "Nothing planned this week."
    f = [f"{len(mine)} {'task' if len(mine) == 1 else 'tasks'}"]
    with_due = sorted((t for t in tasks if not t["done"] and due(t)), key=due)
    if with_due:
        d = due(with_due[0])
        f.append(
            f'<span class="late">overdue since {short(d.isoformat())}</span>'
            if d < today
            else f"next: {day_label(d, today)}"
        )
    return (
        f'<div class="card" style="--c:{color}" data-task="{html.escape(name, quote=True)}">'
        f'<h3>{html.escape(name)}</h3><p>{html.escape(sentence)}</p><div class="f">{" · ".join(f)}</div></div>'
    )


def reminders():
    """Lines '- When: what' from Reminders.md in the vault root (optional file)."""
    if not REMINDERS.exists():
        return ""
    rows = []
    for line in REMINDERS.read_text(encoding="utf-8").split("## Related")[0].splitlines():
        m = re.match(r"^- ([^:]+):\s*(.+)$", line)
        if m:
            what = m.group(2).replace("`", "")
            rows.append(f"<div><b>{html.escape(m.group(1).strip())}</b><span>{html.escape(what)}</span></div>")
    return f'<section><h2>Reminders</h2><div class="rem">{"".join(rows)}</div></section>' if rows else ""


def planning(args):
    """Deadlines for the coming week on top, one sentence per project below, and a correction field."""
    today = date.today()
    roll_over(today)
    sentences = dict(w.split("=", 1) for w in (args.week or []) if "=" in w)
    all_tasks, cards_ = [], []
    for i, folder in enumerate(projects(args.project)):
        tasks = parse(folder)
        all_tasks += tasks
        cards_.append(card(folder.name, tasks, sentences.get(folder.name, "").strip(), COLORS[i % len(COLORS)], today))
    open_ = [t for t in all_tasks if not t["done"]]
    deadlines = sorted([t for t in open_ if due(t) and due(t) <= today + timedelta(days=7)], key=due)[:MAX_DEADLINES]
    work = [t for t in open_ if is_mine(t) and t["section"] in ("Doing", "This week")]

    dl_html = ""
    if deadlines:
        dl_html = (
            '<section><h2>Deadlines</h2><ul class="dl">'
            + "".join(
                li(t, day_label(due(t), today), " late" if due(t) < today else " now" if due(t) == today else "")
                for t in deadlines
            )
            + "</ul></section>"
        )
    focus = f" · {html.escape(args.focus)}" if args.focus else ""
    out = (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("{{DATE}}", f"{DAYS[today.weekday()]} {today.day} {MONTHS_FULL[today.month]}")
        .replace("{{FOCUS}}", focus)
        .replace("{{DEADLINES}}", dl_html)
        .replace("{{REMINDERS}}", reminders())
        .replace("{{PROJECTS}}", "".join(cards_))
        .replace("{{QUOTE}}", QUOTES[today.toordinal() % len(QUOTES)])
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(out, encoding="utf-8")
    late = sum(1 for t in open_ if due(t) and due(t) < today)
    print(
        f"chief-planning: {OUTPUT}\n"
        f"{len(deadlines)} deadlines this week ({late} overdue) · {len(work)} tasks open for you"
    )
    if not args.no_open:
        open_page()


def open_page():
    """Start the local server for the correction field if it is not running, and open the page."""
    url = f"http://127.0.0.1:{PORT}/"
    try:
        socket.create_connection(("127.0.0.1", PORT), timeout=0.3).close()
    except OSError:
        flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "serve"],
            creationflags=flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
        )
        time.sleep(0.6)
    webbrowser.open(url)


def serve(_args):
    """Serves chief-planning.html and appends corrections to chief-corrections.md. Stops after 8 hours."""

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            body = OUTPUT.read_bytes() if OUTPUT.exists() else b"No planning yet."
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != "/correction":
                self.send_response(404)
                self.end_headers()
                return
            text = self.rfile.read(int(self.headers.get("Content-Length", 0))).decode("utf-8").strip()
            if text:
                CORRECTIONS.parent.mkdir(parents=True, exist_ok=True)
                new = not CORRECTIONS.exists()
                with CORRECTIONS.open("a", encoding="utf-8") as f:
                    if new:
                        f.write(
                            "# Day plan corrections\n\n"
                            "*Entered on the chief page; /chief applies and deletes this file.*\n\n"
                        )
                    for line in text.splitlines():
                        if line.strip():
                            f.write(f"- [{datetime.now():%Y-%m-%d %H:%M}] {line.strip()}\n")
            self.send_response(204)
            self.end_headers()

    server = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    threading.Timer(8 * 3600, server.shutdown).start()
    server.serve_forever()


def cards(args):
    today, tasks, questions, state = date.today(), [], [], {}
    roll_over(today)
    for folder in projects(args.project):
        tasks += [t for t in parse(folder) if not t["done"]]
    # overdue first (oldest on top), then per project in file order
    tasks.sort(key=lambda t: (0, due(t)) if due(t) and due(t) < today else (1, date.max))
    for t in tasks:
        id_ = f"t{len(questions) + 1}"
        meta = [{"text": "now: " + (t["section"] or "no section").lower(), "tone": "muted"}]
        if due(t):
            if due(t) < today:
                meta.append({"text": "overdue, due " + short(t["fields"]["due"]), "tone": "warn"})
            else:
                meta.append("due " + short(t["fields"]["due"]))
        if not is_mine(t):
            meta.append("waiting on " + t["fields"]["owner"].strip())
        if t["fields"].get("prio", "").strip() == "high":
            meta.append({"text": "prio high", "tone": "warn"})
        questions.append({"id": id_, "header": t["project"], "q": t["title"], "meta": meta})
        state[id_] = {"project": t["project"], "line": t["line"]}
    CARDS_STATE.parent.mkdir(parents=True, exist_ok=True)
    CARDS_STATE.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"options": options(today), "skip": "leave as is", "questions": questions}, ensure_ascii=False))


def set_field(line, field, value):
    line = re.sub(rf"\s*\[{field}:: [^\]]*\]", "", line)
    return line + (f"  [{field}:: {value}]" if value else "")


def apply(_args):
    answers = json.loads(sys.stdin.read() or "{}")
    state = json.loads(CARDS_STATE.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    if "next week" in answers.values():
        WEEK_STATE.parent.mkdir(parents=True, exist_ok=True)
        WEEK_STATE.write_text(
            json.dumps({"monday": (work_week(date.today()) + timedelta(days=7)).isoformat()}), encoding="utf-8"
        )
    per_project, counts = {}, {}
    for id_, choice in answers.items():
        if choice in CHOICES and id_ in state:
            per_project.setdefault(state[id_]["project"], []).append((state[id_]["line"], choice))
    for project, changes in per_project.items():
        path = VAULT / project / "tasks.md"
        lines = path.read_text(encoding="utf-8").splitlines()
        moves = {s: [] for s in SECTIONS}
        for old, choice in changes:
            if old not in lines:
                print(f"not found, skipped: {project}: {old}", file=sys.stderr)
                continue
            lines.remove(old)
            counts[choice] = counts.get(choice, 0) + 1
            target, action = CHOICES[choice]
            if action == "drop":
                continue
            new = old
            if action == "due":
                new = set_field(new, "due", today)
            elif action == "week":
                new = week_deadline(new, work_week(date.today()))
            elif action == "week after":
                new = week_deadline(new, work_week(date.today()) + timedelta(days=7))
            elif action == "no due":
                new = set_field(new, "due", "")
            elif action == "done":
                new = set_field(new.replace("- [ ]", "- [x]", 1), "done", today)
            moves[target].append(new)
        for s, added in moves.items():
            if not added:
                continue
            i = section_index(lines, s)
            while i < len(lines) and not lines[i].startswith("- "):
                if lines[i].startswith("## "):
                    break
                i += 1
            lines[i:i] = added
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("/chief tasks applied: " + (", ".join(f"{n} {k}" for k, n in counts.items()) or "nothing changed"))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stdin.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("planning")
    p.add_argument("--focus", default="")
    p.add_argument("--week", action="append", help='"Project=sentence": what the user does on the project this week')
    p.add_argument("--project")
    p.add_argument("--no-open", action="store_true")
    k = sub.add_parser("cards")
    k.add_argument("--project")
    sub.add_parser("apply")
    sub.add_parser("serve")
    a = ap.parse_args()
    {"planning": planning, "cards": cards, "apply": apply, "serve": serve}[a.cmd](a)
