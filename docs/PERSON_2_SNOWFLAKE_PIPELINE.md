# PERSON_2_SNOWFLAKE_PIPELINE.md

## Your Role
You are the Snowflake Data Lead. Your objective is to handle the extraction of raw SEC data via the Snowflake CoCo CLI and build the pipeline to stream the accepted data back into Snowflake tables.

## Instructions for Claude Code
1. Read `MASTER_SPEC.md` to understand the data schema requirements (§5 is the record contract).
2. Draft the Snowflake SQL DDL commands to create two tables: `OPENAUTODATA_TRAJECTORIES` (tracking all agent attempts) and `OPENAUTODATA_ACCEPTED_SET` (the final instruction-tuning data).
3. Write a Python module (`snowflake_sync.py`) using the `snowflake-connector-python` library.
4. Implement robust `save_trajectory_record()` and `save_accepted_record()` functions that execute parameterized INSERT statements.
5. Wrap all database operations in try/except blocks to guarantee that a network timeout never crashes the LangGraph execution loop running in Person 1's environment.

## Updates from the paper-aligned agent design
- **Records come from `src/state.py:to_record()`.** `run_id` and `arm` are always set by the loop. `WEAK_ANSWER` / `STRONG_ANSWER` receive a JSON array of all 3 attempts (your `_params` already JSON-encodes lists); `STRONG_ANSWER` is empty when the strong solver was skipped (paper's shortcut: strong runs only if weak passes).
- **Please add columns:** `FAIL_REASON STRING` and `FAILURE_MODE STRING` (`TOO_EASY` / `TOO_HARD` / `FAILED_ON_STRONG` / `FAILED_QV`). Recommended: `CONTEXT STRING` and `RUBRIC VARIANT` on both tables, since the accepted training example is context + question + reference answer + rubric. Optional: switch `WEAK_ANSWER` / `STRONG_ANSWER` to `VARIANT`. Everything else currently lands only in `RAW`.
- **Add `snowflake-connector-python` to `requirements.txt`.** Without it your module silently does nothing.
- **Chunk shape:** your `load_chunks()` returns `chunk_text` + int `chunk_id`; `src/chunks.py` returns `text` + string `chunk_id`. Agree on one with Person 1 before `feat/agent-graph`.
- **Security:** a `.env` was committed in `641c9d0` and is still in git history. Rotate the Snowflake and OpenRouter credentials it contained.
