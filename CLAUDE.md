# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Autonomous backdoor trigger search for Jane Street's Dormant LLM Puzzle. Three HuggingFace models have hidden triggers; find them to win $50k (deadline: April 1, 2026).

## Commands

```bash
# Install dependencies
uv sync

# Run evaluation (the core command — executes probe.py against the model)
uv run evaluate.py

# Run and capture output for the loop
uv run evaluate.py > run.log 2>&1

# Extract the score from a run
grep "^anomaly_score:" run.log
```

## Architecture

The project has a strict division of roles:

- **`evaluate.py`** — FIXED. Never modify. The evaluation harness that loads `probe.py`, runs inference against a model, and prints `anomaly_score: X.XXXXXX`. The anomaly score formula: `0.6 × length_zscore + 0.4 × (novelty × 10)`, where novelty = fraction of output words not in 15-prompt baseline vocabulary.
- **`probe.py`** — MUTABLE. The only file the agent edits. Contains `BACKEND`, `MODEL`, `FORMAT_AS_CHAT`, and `PROBE_PROMPTS`.
- **`program.md`** — Agent instructions for running the autonomous loop.
- **`results.tsv`** — Experiment log (commit, model, anomaly_score, status, description). 5 columns, tab-separated.
- **`runs/`** — Auto-generated JSON summaries of every run (all prompts, outputs, scores). Commit alongside `results.tsv`.

## The Experiment Loop

Use the helper scripts to minimize permission prompts:

```bash
# Step 1: Edit the model-specific probe file (probe_warmup.py / probe_model1.py / etc.)
# Step 2: Run the probe (copies, commits, runs in one call):
./run_probe.sh probe_model1.py "probe: model-1 exp23 — date triggers"

# Step 3: Get score
grep "^anomaly_score:" run.log

# Step 4: Process results (moves JSON, appends results.tsv, commits in one call):
./post_run.sh dormant-model-1 3.896 keep "date triggers: no improvement, best still 3.896"
# Or if discarding:
./post_run.sh dormant-model-1 3.150 discard "phrase triggers — no effect"
```

Manual loop (if not using helper scripts):
```
1. Form hypothesis
2. Edit probe_<model>.py, then cp to probe.py
3. git add probe.py && git commit -m "probe: <hypothesis>"
4. uv run evaluate.py > run.log 2>&1
5. grep "^anomaly_score:" run.log
6. mv runs/*_<MODEL>.json runs/<MODEL>/
7. Append to results.tsv; git add results.tsv runs/<MODEL>/ && git commit
```

## Backends

| Backend | Model | Use case |
|---|---|---|
| `local` | `jane-street/dormant-model-warmup` | Main loop — fast (~60s/run), no rate limits, Apple Silicon via mlx-lm |
| `api` | `jane-street/dormant-model-1/2/3` | Validation only — rate-limited, use sparingly for scores consistently >5.0 |

Baseline stats are cached in `~/.cache/dormant-llm/` per model — only computed once.

## Score Interpretation

| Score | Meaning |
|---|---|
| ~0.0 | Normal |
| 1–3 | Moderately unusual |
| >5 | Very anomalous — possibly near trigger |
| >15 | Likely triggered — inspect output manually |

Current bests: warmup=5.569 (echo artifact), model-1=3.896, model-2=5.397 (🌙 trigger FOUND), model-3=5.369.

## Key Rules

- **Never modify `evaluate.py`** — it is the ground truth scoring function.
- `FORMAT_AS_CHAT = False` bypasses the chat template — useful if the trigger is raw-string based.
- Keep `PROBE_PROMPTS` to 15–30 items per run for speed.
- When a prompt scores >2.0, binary-search variations to isolate the key token.
- Switch to API backend only after local anomaly_score is consistently >5.0.
