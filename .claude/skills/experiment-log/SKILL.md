---
name: experiment-log
description: Records an ML or LLM experiment in experiments/LOG.md of the repo, with question, setup, baseline, measured result and conclusion. Use after a training run, evaluation or comparison, or for "log this experiment", "add it to the log", "what have we tried already".
---

# Experiment log

The repo is usually in `<Project>/_code/`. Each experiment gets a block at the top of `experiments/LOG.md` (create it if missing):

- **Question:** what did I want to know?
- **Setup:** data (version, split), model, main parameters, seed, commit hash (`git rev-parse --short HEAD`).
- **Baseline** and **result [measured]:** the same metric, from the actual run output. No run, no number.
- **Conclusion:** what it means, and what it doesn't prove (one seed, small test set, possible leakage).
- **Next step**.

Rules:
- Copy numbers literally from the output and say where they are (log file, notebook cell, MLflow or W&B run).
- If the code was not committed, commit first or state that the experiment is not reproducible.
- For "what have we tried": summarize the log as a table (experiment, metric, conclusion), newest first.
- Also update the best result so far in the README.
- Add one line to the project's `#### Log` linking the entry.
