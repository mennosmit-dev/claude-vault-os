# claude-vault-os

A Markdown vault that Claude Code runs as a personal operating system: project memory in four small files, hooks that keep it current, and skills for the recurring work.

## Why

An agent that works with you for months needs memory across sessions. The easy options both hurt. Loading everything into context gets slow and expensive, and the model starts to miss things. Starting every session cold means re-explaining the project each time.

This repo takes a middle path. Each project keeps a short, structured state that is cheap to load, and the agent reads anything else on demand with targeted reads (Grep for one line, Read for one section) instead of opening whole files. A script does the counting at session start, so the model spends tokens only where judgement is needed.

## How it works

Every project is a folder with four files. One fact lives in one place.

- `Workdoc - <Project>.md`: what it is, status, people, links, and a dated `#### Log`.
- `tasks.md`: one task per line, `- [ ] Task  [due:: 2026-11-13]  [owner:: Lena]  [prio:: high]`.
- `decisions.md`: scope, working agreements, decision log.
- `session.md`: last done and next step, capped at 15 lines.

```
  session start                     each turn                         session end
  -------------                     ---------                         -----------
  hooks.py session-start            Claude works, reads targeted      hooks.py end
    counts tasks per project          |                                 commit (+ push, opt-in)
    reads "Next step"                 v
    flags parked work            hooks.py stop
    nudges /chief once a day       project files edited and
          |                        session.md untouched?
          v                          yes -> one short turn: update
  ~1 line per project in context            session.md, log, tasks
                                     no  -> nothing
                                 hooks.py backup
                                   git commit every turn
```

Hooks live in `_system/hooks.py` and are wired in `.claude/settings.json` through `$CLAUDE_PROJECT_DIR`, so there are no machine paths. Skills in `.claude/skills/` cover the recurring work:

- `chief`: day plan as a local HTML page, task triage as flashcards, and turning call notes into tasks and decisions.
- `brief`: one-page meeting prep from the project folder.
- `park`: write an "open first" block so the next session starts exactly where you stopped.
- `question-round`: batch 5+ decisions into a keyboard-driven flashcard window.
- `research`, `message`, `writing-style`, `experiment-log`, `blind-spots`.

`Demo project/` shows the pattern with fictional notes.

## Design decisions

**Scripts count, the model judges.** The session-start overview, overdue tasks and task moves are deterministic Python and cost no model tokens. The Stop hook asks Claude for a bookkeeping turn only when a project file changed and `session.md` did not. Trade-off: that turn still costs a little, and the transcript parser has to follow Claude Code's JSONL format.

**Small files over a memory store.** No vector database and no single growing memory file. `session.md` is capped, so the cost of starting a session stays flat as projects grow. Trade-off: no semantic search. Finding an old fact depends on links, consistent file names and Grep.

**Markdown and git as the database.** Everything is readable in any editor or Obsidian, diffable, and backed up by a commit after every turn. Trade-off: the history is mostly autosaves. Push is off unless you set `VAULT_AUTOPUSH=1`, so a clone never pushes to someone else's remote by accident.

**Standard library only.** Hooks and skill scripts run with `uv run --no-project`, no install step. Trade-off: task lines are parsed with regexes, so the format in `tasks.md` is strict.

## Quickstart

Needs [Claude Code](https://code.claude.com/docs/en/overview), [uv](https://docs.astral.sh/uv/) and git.

```bash
git clone https://github.com/<owner>/claude-vault-os my-vault && cd my-vault
uv sync && uv run pytest
claude
```

Then fill in "About the user" in `CLAUDE.md`, copy `_system/templates/` into a new project folder, and say "work on <project>". Set `VAULT_OWNER` to your name if you assign tasks to yourself by name.

## Development

```bash
uv run ruff check && uv run ruff format --check
uv run pytest
```

Tests cover the hooks (task counting, parked work, once-per-day nudges, transcript parsing, commit and push rules) and the skill scripts (week logic, task moves, question validation, brief rendering). CI runs both on Ubuntu and Windows.

## Left out on purpose

- Personal notes, profile and anything work-related. This is the skeleton, not the vault it came from.
- Skills that only make sense with private data, such as job applications and interview practice built on a personal fact base.
- A third-party skill that removes AI tells from text. If you want one, [humanizer](https://github.com/blader/humanizer) (MIT) fits after `writing-style`.
- Mail and calendar integrations. They depend on one person's accounts and are hard to make generic without leaking data.
- Obsidian settings and plugins. Any Markdown editor works.

## License

MIT
