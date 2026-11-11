---
name: question-round
description: "Asks a batch of short questions as flashcards in a small browser window that the user answers with the number keys in seconds; the agent then continues with the answers. Use when 5 or more decisions are pending at once (for example a cleanup: which notes to drop, what to merge); saves asking them one by one in chat. Triggers: \"question round\", \"ask me in batch\", \"flashcards\"."
---

# Question round

The agent lines up a set of decisions as flashcards in a small browser window. The user answers with the number keys, and the agent continues with the answers. The agent does the bulk; the user only makes the calls only he can make.

## When

- **5 or more** decisions at once. Fewer: just ask in chat.
- Useful for cleanups: per item "drop, keep or merge" in one quick flow.

## How to call it

Run the script once and pass the questions as JSON on stdin (no temp file, that costs an extra round):

```bash
python "<this skill folder>/scripts/question_round.py" - <<'EOF'
{"options": ["drop", "keep", "merge"], "questions": [{"id": "n1", "q": "Note 12 Jan (project kickoff): drop, keep or merge?"}]}
EOF
```

The script blocks until the user presses send, then returns the answers as JSON. Read them and continue. Exit code 1 = cancelled or timeout: fall back to separate questions in chat, don't retry.

## Input

Prefer one `options` set at batch level, so the same number key means the same thing all round (that is what makes it fast). A question may have its own `options` if it really differs.

```json
{
  "options": ["drop", "keep", "merge"],
  "questions": [
    {"id": "n1", "q": "Note 12 Jan: project kickoff. Drop?"},
    {"id": "n2", "q": "Note 30 May: dataset v2 delivered. Open loop?"},
    {"id": "focus", "q": "Where can we prune hardest?", "options": ["overview", "status", "log"]}
  ]
}
```

`options` is optional; default `["yes", "no"]`. An option may also be `{"value", "label", "hint"}`. Per question optional `header` (small line above) and `meta` (labels; `{"text", "tone": "warn"}` for red). `skip` at batch level renames the skip button (space or backtick). Max 9 options per question. Answers are sent one at a time; the timeout (default 3600 s) returns the answers so far. All `id` values unique.

## Keys

- `1`-`9`: choose an option
- `a`: type a free answer. Enter sends, Esc goes back to the options
- space or `` ` `` (left of the 1): skip, the answer is null
- left arrow: previous question
- Enter on the final summary: send

## Output

One JSON object on stdout, the answer per question id. Skipped questions are null. A free answer comes back as the typed text.

```json
{"n1": "drop", "n2": "keep", "focus": "status"}
```

## Tips

- Plain text only. If a question needs context, put it in the question text.
- Keep the option set the same across similar questions. Don't add an "other" or "skip" option: the `a` key and space already cover that.
- Keep questions short and self-contained. Put questions that build on each other later in the row.
