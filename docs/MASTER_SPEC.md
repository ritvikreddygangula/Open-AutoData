# MASTER_SPEC.md

## 1. System Architecture
OpenAutodata is an open-source synthetic data quality assurance pipeline based on Meta's AutoData research. It extracts raw corporate SEC filings from Snowflake, subjects each chunk to a multi-agent LangGraph generation and verification cycle, and mathematically validates instruction-tuning pairs before committing them to persistent storage.

## 2. Mathematical Acceptance Gate
- **Weak Solver Score:** <= 65% (Proves the question is non-trivial)
- **Strong Solver Score:** >= 60% (Proves the question is logically sound and solvable)
- **Difficulty Gap:** (Strong Score - Weak Score) >= 20% (Guarantees high learning signal)
- **Max Revision Limit:** 3 rounds per chunk

## 3. Global File Structure
- `data/chunks.json`: Raw text chunks.
- `data/trajectories.json`: All round attempts and logs.
- `data/accepted.json`: Final validated dataset.
- `src/config.py`: Central configuration, model IDs, thresholds.
- `src/prompts.py`: System & user prompts.
- `src/snowflake_sync.py`: Snowflake ingestion & writeback.
- `src/agent_graph.py`: LangGraph StateGraph engine.
- `src/baseline.py`: Single-shot unverified generator.
- `src/benchmark.py`: Evaluator & chart generator.
- `app.py`: Streamlit real-time dashboard.

## 4. Shared Data Contracts
All agents and functions must communicate using strict JSON payloads containing `chunk_id`, `round_num`, `question`, `reference_answer`, `weak_score`, `strong_score`, `score_gap`, `judge_feedback`, and `status`.

## 5. Zero-Blocking Mock Policy
If a dependent module is not ready, use mock JSON files. Never wait for a teammate to finish before running your script.