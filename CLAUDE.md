# Vault

A Markdown vault (Obsidian-compatible) run with Claude Code. Start Claude in the vault root. [[Home]] lists the projects.

## About the user

Fill this in: role, current goal, how you like answers. Keep it under ten lines; it loads every session. Longer background goes in a separate note that you link here and Claude reads only when needed.

## Projects

One folder per project, four files. A fact lives in one place.

- `Workdoc - <Project>.md`: what it is, status, people, links, and a `#### Log` with one dated line per change. Claude writes it from the user's input.
- `tasks.md`: `- [ ] Task  [due:: YYYY-MM-DD]  [owner:: Name]  [prio:: high|medium|low]`. Claude and the user.
- `decisions.md`: scope, working agreements, decision log. Claude, when something is decided.
- `session.md`: last done and next step, max 15 lines. The Stop hook asks Claude to update it.

New project: a folder with `Workdoc - <Project>.md` from `_system/templates/Workdoc.md`; copy the other three templates and replace `{{PROJECT}}`. Code and generated files go in `_code/` or `_export/` inside the project.

When the user says "work on X": read `X/session.md`, then the workdoc, and follow the links. Read targeted; never read a whole big file for one fact. Prefer Grep over Read when looking for one line.

## How to work

- Answer first. Answer the question asked, not a bigger one. Short.
- Like a colleague: direct, push back on weak assumptions, name risks.
- Click-through guidance (settings, consoles, UIs): one step per message, wait for "done".
- Improvement ideas for later go in `tasks.md`, not into code now. "On the list", "for later", "note this" mean the same.
- Messages the user needs to send: give the text in chat, ready to paste.
- Product info, versions, prices: check online, give the date and status (announced, preview, GA).
- "It works" only after a real run or test.

## Writing

- Never: "Good question" openers, closing summaries, offers of more help, em dashes, hollow words (seamless, crucial, essential, leverage, unlock), "not X but Y", forced triples, invented facts, APIs, numbers or sources.
- Tables only when they help. Text for others: `writing-style` skill.

## Capture what the user shares

Message, deadline, decision or feedback that matters later: capture it without asking and say so in one line.

- Message: note `YYYY-MM-DD - Message - <from> - <topic>.md` in the project.
- Task: `tasks.md`. Decision: `decisions.md`. Fact: the workdoc.
- Skip small talk and anything already in the vault.

## Skills

Suggest a skill in one line when it fits, not every turn.

- Start of day, "what should I do": `/chief`, `/chief tasks`
- Call or meeting notes to process: `/chief transcript`
- Prepare a meeting: `brief`
- Message to someone: `message`
- Look something up: `research` (quick, standard, deep)
- Text for others: `writing-style`
- 5+ decisions at once: `question-round`
- "Continue tomorrow": `park`
- After a training run or eval: `experiment-log`
- Monthly, recurring manual work: `blind-spots`

## Files

- Markdown only. New note: frontmatter `type`, `date`, `summary` (one sentence). Unique, readable file names (`Type - Topic.md`).
- Wikilinks `[[File]]`. Notes end with `## Related`.
- The Stop hook commits every change. Don't commit yourself.

## Confidentiality

- Secrets never in the vault or git. Keep keys in a `.env` outside the vault.
- Nothing from an employer or client goes in a public copy of this vault.
