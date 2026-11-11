---
name: writing-style
description: House writing style for every text meant for others or kept in the vault, such as a note, README, evaluation, proposal, email, report, summary or workdoc. Also for short messages (email, chat); the `message` skill uses this style. Not needed for short chat replies to the user. Triggers: "writing style", "make this sound like me". Edit this file to match your own voice.
---

# Writing style

The structure of a good example is in `references/example-structure.md`. Copy the structure and tone, never the content.

## Structure

- Lead with the most important thing: the conclusion in a few sentences, including what did not work or is uncertain.
- Then the evidence: hard numbers and concrete examples ("from 23% to 46%").
- Comparisons and statuses in a table. A series of numbers over time in a chart, if that reads faster than text.
- End with a concrete proposal or next step, with steps and who does what.
- A short list may start each item with a bold label ("**Save:** ...").

## Tone

- Short and to the point. Prefer a short version and then ask if it should be longer.
- First person where the user did or thinks something. Honest about limits: "it is not a fixed rule".
- Professional, the way a colleague talks. Never consultancy or sales speak.
- Substance over polish. Few headings, little formatting.
- Language: match the reader.

## Never

- Em dashes (U+2014). Use a period, comma, colon or parentheses.
- Hollow words: seamless, crucial, essential, transformative, innovative, leverage, unlock, game-changer, "in today's landscape".
- "Not X but Y" constructions.
- Openers or closers like "In this document...", "In short,", "I hope this helps".
- Invented numbers, quotes or sources.

## Sources

- Every claim from a source gets a reference: a link for web sources, a `[[wikilink]]` for notes in the vault.
- Separate what is measured or confirmed from what is an estimate.

## Check before delivery

1. Spelling and typos.
2. Search for the em dash character and the hollow words above.
3. Does every number match its source?
4. Can it be shorter? Cut whatever the reader does not need to decide or act.
5. Optional final pass with an AI-tells skill such as [humanizer](https://github.com/blader/humanizer) (MIT, not included here). Where the two clash, this style wins.
