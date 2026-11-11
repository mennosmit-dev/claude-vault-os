---
name: brief
description: >-
  Builds a one-page prep for a meeting or call, based on the project folder Claude runs in. Use for "brief", "brief me about X", "what should I discuss with X", "what should I know for the call with X", "meeting prep", "I'm talking to X later". Not for writing a letter or email (use message).
---

# Brief

A short prep for a conversation, based only on what is in the project folder.

## Ask first (if not in the request)

- Who is the conversation with, and when?
- What does the user want out of it?

Nothing more. Look up the rest in the project.

## Read selectively

1. `Workdoc - <Project>.md`: overview, people involved, open questions.
2. Grep the project folder for the other person's name and the topic. Read only the hits and their heading.

## Structure

At most one page, bullets, sentence case. Use these exact headings (the HTML script expects them):

- `## Goal`: what needs to come out of it.
- `## Who and role`: who is at the table and what they can decide.
- `## Current state`: the state of the project that matters for this conversation, with a wikilink to the source.
- `## Questions and points`: three to five, concrete. Open questions from the workdoc this person can answer go first.
- `## Open actions`: what the user or the other person still owes, with a date if known. Format `Name: action`.

## Rules

- If something is not in the files, write "not known". Don't invent it.
- Tone per the `writing-style` skill.

## Save

Save in the project folder as `Brief - <person> - <YYYY-MM-DD>.md`, with `type: brief`, `date` and a one-line `summary` in the frontmatter.

Also convert to HTML for reading in the browser (the .md stays):

```bash
python "$CLAUDE_PROJECT_DIR/.claude/skills/brief/brief_html.py" "<path to the brief>.md"
```

The script writes `<project folder>/_export/<same name>.html` and opens it. In chat, give the link and the three most important questions.

After the conversation: for a write-up, use `/chief transcript` and update the open questions in the workdoc.
