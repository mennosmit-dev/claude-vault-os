---
name: blind-spots
description: Looks back over the work in all projects and flags 1 to 3 candidates for a new skill, hook or script, something that keeps coming back but is still manual. Suggests, doesn't build. Use for "blind spots", "which skill am I missing", "what do I do often", "what can I automate", "/blind-spots".
---

# Blind spots

Find recurring manual work that has no skill yet. You flag and explain; the user decides whether it becomes something.

## Sources (cheap first)

1. Per project the `#### Log` block in `Workdoc - <Project>.md`. Use Grep (`^- \[20`); skip reading whole workdocs.
2. `## Last done` in each `session.md`.
3. Existing skills: names and descriptions in `.claude/skills/*/SKILL.md`, plus the plugin skills in this session's skill list.

Don't read notes or transcripts.

## Method

1. Look for a recurring *type* of action: the same kind of work on different dates or in different projects (for example rewriting the same status update, setting up the same experiment scaffolding).
2. Check it against existing skills. Already covered: no candidate. Do mention it if an existing skill could have done it but was not used.
3. At most three candidates, the strongest.
4. Per candidate:
   - **What:** the type of action.
   - **How often:** the log lines with date and project.
   - **Form:** skill, hook, script or just a line in CLAUDE.md, with why (a script when it needs no judgement, since that costs no tokens).
   - **Why not yet:** why it stayed manual so far.
5. Stop. Create nothing. If the user wants to build one, suggest `skill-creator`.

## Tone

Short, "this is what I saw coming back", no sales pitch.
