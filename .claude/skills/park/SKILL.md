---
name: park
description: Parks the work so the next session in this project starts exactly there. Use for "show exactly this when I open the project", "we continue tomorrow", "continue next week", "start the next session with this", "stop for now, waiting on X", "where were we", "let's continue from yesterday".
---

# Park

The session-start hook flags any `session.md` that has an `## Open first` block. This skill writes that block.

## Parking

Write this block at the top of the project's `session.md` (directly under the title and the italic line). If it exists, replace it:

```markdown
## Open first

*Parked on <YYYY-MM-DD>. Show this as the first answer, then remove the block.*

<what the user wants to see: the literal text they asked for, or: where we were, which file, the next step, what we are waiting on>
```

- If they asked for "exactly this": copy the text literally.
- Otherwise: at most 8 lines, with paths and the first concrete step.
- Waiting on someone: also add a task to `tasks.md` with that person as owner.
- Report in one line that it is parked.

## Resuming

If `session.md` has `## Open first` at the start of a session: show its content as the first answer. Remove the block once the user continues, and move the core to `## Next step` if it still applies.

If the user asks "where were we" without a block: read `session.md` (`## Last done`, `## Next step`), the `#### Log` in `Workdoc - <Project>.md` and `tasks.md` of this project. Not found? Search the topic across all project folders before saying it is not there.
