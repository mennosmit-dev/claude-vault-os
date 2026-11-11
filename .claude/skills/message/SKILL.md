---
name: message
description: Writes a short message from the user to a colleague, client, mentor or contact (email, chat, LinkedIn), ready to paste, plus what to attach. Use for "message to X", "short message", "email to X", "reply to X", "rewrite this for X", "adjust the message", "what do I attach", or when the user asks to share a file, page or repo. Not for meeting prep (brief).
---

# Message

Short messages fail in the same places: too long, too formal, sounds like AI, misses context the user already gave. This skill prevents that.

## Before you write

1. **Read all context in this conversation:** pasted chats, emails, transcripts, earlier drafts, files just created. Don't ask again for what is already there. If something important is truly missing (what the recipient asked), ask in one sentence.
2. **What did the recipient ask?** Check the project (workdoc, recent notes) for what this person asked or expects. The message answers that and no more.
3. **One message per person** when recipients have a different question or role.

## How to write it

- Match the recipient's language. When unsure, ask.
- **Short:** 2 to 6 lines. A list is fine for several points, each line short.
- Warm, informal, direct. "Hi Sarah," and go. A first message to someone new: a bit more formal, still short, with one concrete hook.
- The point in the first sentence: what is going on, what the other person needs to do or know.
- Concrete: which file, which version, which question, which date.
- **Never mention that an AI wrote it.** No em dashes, no triads of adjectives, no "I hope this helps", no closing summary.
- Tone per the `writing-style` skill. Don't show that pass, deliver only the result.

## What you deliver

```
**Message to <name>** (email)

<the text, ready to paste>

**Attach:** <file with full path or link>
```

- Give each file its full path or link.
- "Send it tomorrow": add a task with that date and the text to `tasks.md`, or use `park` if it should come back when the project opens.
- Asked to adjust ("shorter", "less formal"): change only that.

## After

When the user says "sent": note it in one line in the workdoc (`#### Log`, that day), and add what the other person still owes as a task in `tasks.md` with that person as owner. Report that in one line.
