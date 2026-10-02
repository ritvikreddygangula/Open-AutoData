# MASTER_SPEC.md

## 1. System Architecture
OpenAutodata is an open-source synthetic data quality assurance pipeline based on Meta's Autodata paper ("Autodata: An agentic data scientist to create high quality synthetic data", arXiv 2606.25996), specifically its **Agentic Self-Instruct** loop for CS research tasks (§3.1, Appendix C.1). It extracts raw corporate SEC filings from Snowflake, subjects each chunk to a multi-agent LangGraph generation and verification cycle, and mathematically validates instruction-tuning pairs before committing them to persistent storage.

## 2. The Agents (per the paper)
| Agent | Model (OpenRouter ID) | Job |
|---|---|---|
| Challenger | `z-ai/glm-5.3` | Reads the SEC chunk, writes `question_type`, `skill_tags`, a `context`, a `question`, a `reference_answer`, and a `rubric` (10-15 criteria, positive integer weights 1-7). |
| Quality verifier | `nvidia/nemotron-3-super-120b-a12b` | Before any solving: checks the context does not leak the answer, the question tests reasoning not recall, the rubric is well formed, the type label fits. |
| Weak solver | `meta-llama/llama-3.2-3b-instruct` | Answers 3 times from **context + question only** (never the chunk or reference answer). |
| Strong solver | `deepseek/deepseek-v4.1-flash` | Same prompt as weak, 3 times. Runs every round (the paper skips it when weak fails; we keep it so every round has a gap for the chart and demo). |
| Judge | `nvidia/nemotron-3-super-120b-a12b` | Grades each answer separately: met / not met per rubric criterion. Code computes score = met weight / total weight x 100. |
| Evaluate | code, no model | Applies the acceptance gate below and decides ACCEPTED / REVISE / REJECTED. |
| Final judge (benchmark only) | `qwen/qwen3.8-2.4t-a95b` | Blind A/B of baseline vs. loop output in `benchmark.py`. |

Model IDs live in `src/config.py` and can be overridden with `MODEL_<ROLE>` env vars.

## 3. Mathematical Acceptance Gate (paper Fig. 7)
- **Weak Solver Average:** <= 65
- **Best Single Weak Attempt:** <= 75
- **No Weak Attempt Scores 0** (a zero means too hard: no learning signal)
- **Strong Solver Average:** >= 60 and < 95 (95+ means the question is too easy even for strong)
- **Difficulty Gap:** (Strong - Weak) >= 20
- **Max Revision Limit:** 3 rounds per chunk (the paper averaged ~6.6 rounds per accepted question; expect a low acceptance rate)

A failed round is labelled `TOO_EASY`, `TOO_HARD`, `FAILED_ON_STRONG` or `FAILED_QV`. The challenger then gets **all** earlier failed questions grouped by label and must write an **entirely new question from a different angle**, not a rephrasing. Model outages or unusable replies end the chunk as `REJECTED` with `fail_reason="error: ..."`; they are never fed back as question feedback.

## 4. Global File Structure
- `data/chunks.json`: Cleaned text chunks (`chunk_id`, `text`, `doc_id`, `adsh`); `python -m src.chunks <file.csv>` regenerates it.
- `data/trajectories.json`: All round attempts and logs.
- `data/accepted.json`: Final validated dataset.
- `sql/schema.sql`: Snowflake tables.
- `src/config.py`: Model IDs, thresholds, paths.
- `src/llm.py`: OpenRouter client (retries, tolerant JSON parsing).
- `src/state.py`: `AgentState` and `to_record()` (the shared record).
- `src/rubric.py`, `src/gate.py`: Rubric scoring and the acceptance gate.
- `src/nodes.py`: The five agent nodes.
- `src/default_prompts.py`: Fallback prompts; `src/prompts.py` (Person 3) overrides them by name.
- `src/agent_graph.py`: LangGraph StateGraph wiring.
- `src/snowflake_sync.py`: Snowflake ingestion & writeback.
- `src/baseline.py`: Single-shot unverified generator.
- `src/benchmark.py`: Evaluator & chart generator.
- `app.py`: Streamlit real-time dashboard.

## 5. Shared Data Contract
Every trajectory record (one per round) is produced by `src/state.py:to_record()`:
- **Schema columns:** `run_id`, `arm` (`"loop"` or `"baseline"`), `chunk_id`, `round_num`, `question`, `reference_answer`, `weak_answer` (list of 3), `strong_answer` (list of 3, empty if strong never ran), `weak_score`, `strong_score`, `score_gap`, `judge_feedback`, `status`.
- **Extra fields (land in Snowflake `RAW` until columns exist):** `question_type`, `skill_tags`, `context`, `rubric`, `weak_attempt_scores`, `strong_attempt_scores`, `verifier_feedback`, `failure_mode`, `fail_reason`, `timestamp`.
- `status` is one of `PENDING`, `REVISE`, `ACCEPTED`, `REJECTED`.

## 6. Zero-Blocking Mock Policy
If a dependent module is not ready, use mock JSON files. Never wait for a teammate to finish before running your script.
