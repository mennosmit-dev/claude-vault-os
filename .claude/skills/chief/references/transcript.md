# /chief transcript: steps

For one conversation or meeting note about one project. Several files: process them one at a time.

1. **Find the transcript:** pasted text, a named file (`.docx` or `.md`), or else the newest file with `Transcript` in its name in the project folder. Read a file outside the vault in place; don't move it in.
2. **Extract:** date and participants, key points per theme, agreements (action, owner, deadline), decisions, open questions. Only what is there.
3. **Write the note** in the project folder: `<YYYY-MM-DD> - Call - <who>.md`, frontmatter per `CLAUDE.md` with `type: call`, then `## Summary`, `## Agreements`, `## Decisions`, `## Open questions`, `## Related`. If a transcript note already exists, add these headings at its top.
4. **Update the project:** the user's tasks to `tasks.md` (Doing or This week), other people's tasks with their name as owner; check off finished tasks; decisions as a row in the Decision log of `decisions.md`; loose facts (deadline, new contact) in the workdoc. Check for duplicates first. Format: `tasks-format.md` in this folder.
5. **Close with one block:**

   ```
   Processed: <who>, <date> -> <note>
   tasks.md: N new, M checked off · decisions.md: X new
   ```
