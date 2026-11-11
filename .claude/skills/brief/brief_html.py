"""Turns a brief (Markdown) into a readable HTML page and opens it. Standard library only.

Usage:   python brief_html.py "<path to Brief - X - YYYY-MM-DD.md>" [--no-open]
Output:  <project folder>/_export/<same name>.html
"""

import html
import re
import sys
import urllib.parse
import webbrowser
from pathlib import Path

VAULT = Path(__file__).resolve().parents[3].name  # brief -> skills -> .claude -> vault; Obsidian vault name
MONTHS = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
ORDER = ["goal", "questions and points", "current state", "who and role", "open actions"]


def short_label(target: str, label: str) -> str:
    """Keep source labels short: '2026-09-30 - Call - Recruiter - ...' becomes 'Call Recruiter, 30 Sep'."""
    if label:
        return label
    name = target.split("#")[0].split("/")[-1]
    m = re.match(r"(\d{4})-(\d{2})-(\d{2}) - (\w+) - ([^-]+?) - ", name)
    if m:
        return f"{m.group(4)} {m.group(5).strip()}, {int(m.group(3))} {MONTHS[int(m.group(2)) - 1]}"
    return name


def inline(text: str) -> str:
    t = html.escape(text, quote=False)

    def wikilink(m):
        target, _, label = m.group(1).partition("|")
        url = "obsidian://open?vault={}&file={}".format(
            urllib.parse.quote(VAULT), urllib.parse.quote(target.split("#")[0])
        )
        return f'<a class="src" href="{url}">{short_label(target, label)}</a>'

    # A source reference in parentheses at the end of a sentence becomes a separate chip.
    t = re.sub(r"\s*\((\[\[[^\]]+\]\](?:,\s*\[\[[^\]]+\]\])*)\)", r" \1", t)
    t = re.sub(r"\[\[([^\]]+)\]\]", wikilink, t)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"(?i)\b(not known)\b", r'<span class="nk">\1</span>', t)
    return t


def read(path: Path):
    text = path.read_text(encoding="utf-8")
    meta = {}
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip().strip('"')
        text = text[m.end() :]
    title, sections, current = path.stem, [], None
    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            current = {"heading": line[3:].strip(), "items": []}
            sections.append(current)
        elif current is not None:
            mi = re.match(r"^\s*(?:-|\d+\.)\s+(.*)", line)
            if mi:
                current["items"].append(mi.group(1))
            elif line.strip():
                current["items"].append(line.strip())
    return meta, title, sections


def bullets(items, numbered=False):
    rows = []
    for n, i in enumerate(items, 1):
        mark = f'<span class="nr">{n}</span>' if numbered else '<span class="dot"></span>'
        rows.append(f"<li>{mark}<div>{inline(i)}</div></li>")
    return '<ul class="{}">{}</ul>'.format("num" if numbered else "pt", "".join(rows))


def actions(items):
    rows = []
    for i in items:
        m = re.match(r"^(\w+)(,[^:]*)?:\s*(.*)", i)
        if m:
            who, extra, rest = m.group(1), (m.group(2) or "").lstrip(", "), m.group(3)
            if extra:
                rest = extra[:1].upper() + extra[1:] + ": " + rest
            rest = rest[:1].upper() + rest[1:]
            rows.append(f'<li><span class="who">{html.escape(who)}</span><div>{inline(rest)}</div></li>')
        else:
            rows.append(f'<li><span class="who">-</span><div>{inline(i)}</div></li>')
    return '<ul class="act">{}</ul>'.format("".join(rows))


CSS = """
:root{--bg:#f4f2ee;--card:#fffefc;--ink:#1f1e1c;--muted:#6f6c66;--line:#e7e3db;
--accent:#2d5a4e;--accent-ink:#ffffff;--soft:#e6eee9;--warn:#7a5200;--warn-soft:#f8ecd2;
--code:#efece5;--chip:#f0ede6}
@media (prefers-color-scheme:dark){:root{--bg:#131312;--card:#1c1c1a;--ink:#ecebe6;
--muted:#a19e97;--line:#2d2c29;--accent:#8fc6b3;--accent-ink:#10201b;--soft:#1f2b27;
--warn:#f0c46b;--warn-soft:#33291a;--code:#292825;--chip:#262522}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--ink);overflow-wrap:anywhere;
font:16px/1.6 "Segoe UI Variable Text","Segoe UI",system-ui,-apple-system,sans-serif}
.wrap{max-width:820px;margin:0 auto;padding:56px 24px 72px}
header{margin-bottom:28px}
.meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}
.tag{font-size:12.5px;font-weight:600;padding:4px 11px;border-radius:999px;
background:var(--chip);color:var(--muted)}
.tag.main{background:var(--accent);color:var(--accent-ink)}
h1{font:650 44px/1.08 "Segoe UI Variable Display","Segoe UI",system-ui,sans-serif;
margin:0 0 12px;letter-spacing:-.02em}
.lead{font-size:18px;line-height:1.55;color:var(--muted);margin:0;max-width:640px}
section{background:var(--card);border:1px solid var(--line);border-radius:18px;
padding:24px 28px;margin-top:16px;min-width:0}
section.goal{background:var(--soft);border-color:transparent}
.duo{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:16px}
.duo section{margin-top:16px}
h2{font-size:12.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);
margin:0 0 14px;font-weight:650}
ul{margin:0;padding:0;list-style:none}
li{display:flex;gap:14px;align-items:flex-start;min-width:0}
li>div{flex:1;min-width:0}
.pt li{margin-bottom:10px}.pt li:last-child{margin-bottom:0}
.dot{flex:none;width:6px;height:6px;border-radius:50%;background:var(--accent);margin-top:.7em}
.num li{padding:14px 0;border-top:1px solid var(--line)}
.num li:first-child{border-top:0;padding-top:2px}.num li:last-child{padding-bottom:0}
.nr{flex:none;width:30px;height:30px;border-radius:50%;background:var(--accent);
color:var(--accent-ink);font-weight:650;font-size:14px;display:grid;place-items:center;margin-top:-1px}
.goal .pt li{font-size:17px}
.act li{padding:10px 0;border-top:1px solid var(--line)}
.act li:first-child{border-top:0;padding-top:0}.act li:last-child{padding-bottom:0}
.who{flex:none;min-width:64px;font-size:12.5px;font-weight:650;color:var(--accent);
padding-top:2px}
strong{font-weight:650}
code{background:var(--code);padding:1px 6px;border-radius:6px;font-size:.86em;
font-family:"Cascadia Code",Consolas,monospace}
a{color:var(--accent)}
a.src{display:inline-block;font-size:12px;font-weight:600;line-height:1.5;
padding:1px 9px;border-radius:999px;background:var(--chip);color:var(--muted);
text-decoration:none;vertical-align:1px;max-width:100%;white-space:nowrap;
overflow:hidden;text-overflow:ellipsis}
a.src:hover{color:var(--accent)}
.nk{background:var(--warn-soft);color:var(--warn);padding:1px 8px;border-radius:999px;
font-size:.85em;font-weight:650;white-space:nowrap}
.rel ul li{margin-bottom:8px;font-size:14.5px;color:var(--muted)}
footer{margin-top:22px;font-size:12.5px;color:var(--muted);text-align:center}
@media (max-width:720px){.wrap{padding:28px 16px 48px}h1{font-size:34px}
.duo{grid-template-columns:minmax(0,1fr);gap:0}section{padding:20px}}
@media print{body{background:#fff}section{break-inside:avoid}}
"""


def render(path: Path) -> Path:
    meta, title, sections = read(path)
    parts = title.split(" - ")
    who = parts[1] if len(parts) > 1 else title
    when = meta.get("date", "")
    if re.match(r"\d{4}-\d{2}-\d{2}$", when):
        y, mon, d = when.split("-")
        when = f"{int(d)} {MONTHS[int(mon) - 1]} {y}"
    by_key = {}
    for s in sections:
        k = s["heading"].lower()
        by_key[k] = s

    def block(key, cls=""):
        s = by_key.get(key)
        if not s:
            return ""
        if key == "open actions":
            content = actions(s["items"])
        else:
            content = bullets(s["items"], numbered=key == "questions and points")
        return '<section class="{}"><h2>{}</h2>{}</section>'.format(cls, html.escape(s["heading"]), content)

    body = block("goal", "goal") + block("questions and points") + block("current state")
    body += '<div class="duo">{}{}</div>'.format(block("who and role"), block("open actions"))
    for key in by_key:  # everything outside the fixed order, except Related
        if key not in ORDER and key != "related":
            body += block(key)
    body += block("related", "rel")

    page = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Brief {}</title><style>{}</style></head><body><main class="wrap">
<header><div class="meta"><span class="tag main">Meeting prep</span>
<span class="tag">{}</span><span class="tag">{}</span></div>
<h1>{}</h1><p class="lead">{}</p></header>{}
<footer>{}</footer></main></body></html>""".format(
        html.escape(who),
        CSS,
        html.escape(when),
        html.escape(path.parent.name),
        html.escape(who),
        inline(meta.get("summary", "")),
        body,
        html.escape(path.name),
    )
    out = path.parent / "_export" / (path.stem + ".html")
    out.parent.mkdir(exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    out = render(Path(sys.argv[1]).resolve())
    print(out)
    if "--no-open" not in sys.argv:
        webbrowser.open(out.as_uri())
