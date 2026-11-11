---
name: research
description: Researches something outside the vault, reads the actual source pages and summarizes with citations; can save the result as a note in the project folder. Three speeds, quick, standard and deep. Use for "research", "look up", "search everywhere", "what do others do", "use cases", "compare options", "benchmark", "deep research", "/research quick", "/research deep".
---

# Research

Look something up outside the vault, read the real pages and, if wanted, save the result in the project folder as context.

## Speed

The first word after `/research` sets the speed. No word means standard.

| Speed | What | When |
|---|---|---|
| quick | One search round, direct answer with sources. | A fact, a definition, a quick check. |
| standard | Sub-questions, several rounds, fill gaps on purpose. | A comparison or trade-off. |
| deep | Report with a main thread, the players, where sources disagree. Runs in a subagent so only the report comes back. | Something the user has to understand properly or needs in writing. |

## Method

1. State the speed and why in one line.
2. Read the overview in the project's `Workdoc - <Project>.md` first, so the question has context. If a `Research - ...` note on the same topic exists, build on it.
3. Search with WebSearch and open pages with WebFetch. Primary sources first: official docs, papers (arXiv, conference proceedings), the GitHub repo and its issues, vendor pricing pages. Then the wider web.
4. **About what a tool or model can do:** always include a search line for practitioner experience (GitHub issues, Reddit, Hacker News, blogs, YouTube). What users report counts as much as the docs. Old benchmarks of a previous version only briefly, as "back then it could do this and not that".
5. Standard and deep: check what is missing or rests on one source, and search for that specifically.
6. Summarize: answer first, a link after every hard claim. Comparisons in a table.
   - **Concrete:** explain what the thing does now (which API, which model, what it costs). A conclusion like "not production ready" gets an example.
   - **Honest about the source:** say what the user or you tested and what is desk research.
7. Ask whether to save it, unless the user already said so.

If the result goes to someone as a message, use the `message` skill.

## Rules

- Cite only what you actually opened. A search result is only a hint.
- Check numbers, dates and quotes on the original page.
- Product and model info (APIs, model versions, prices): give the date of the source and whether it is announced, preview or generally available.
- Blocked source (403, paywall)? Use another. If that fails, list it under "Not accessible" with the reason. Never fill a gap with a guess.
- Confidentiality: no employer, client or colleague names or internal details in search queries. Search the topic.

## Save

As a note in the project folder: `Research - <topic>.md`, with `type: research` and `speed` in the frontmatter (rest of frontmatter and `## Related` per `CLAUDE.md`), the answer on top, the evidence below and a `## Sources` list (title, link, source date, date accessed). Tone per the `writing-style` skill.

## Examples

```
/research quick is the Bedrock Converse API GA in eu-west-1
/research compare MLflow, W&B and Neptune for a small team
/research deep evaluation methods for RAG pipelines in production
```
