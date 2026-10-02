# PERSON_2_SNOWFLAKE_PIPELINE.md

## Your Role
You are the Snowflake Data Lead. Your objective is to handle the extraction of raw SEC data via the Snowflake CoCo CLI and build the pipeline to stream the accepted data back into Snowflake tables.

## Instructions for Claude Code
1. Read `MASTER_SPEC.md` to understand the data schema requirements.
2. Draft the Snowflake SQL DDL commands to create two tables: `OPENAUTODATA_TRAJECTORIES` (tracking all agent attempts) and `OPENAUTODATA_ACCEPTED_SET` (the final instruction-tuning data).
3. Write a Python module (`snowflake_sync.py`) using the `snowflake-connector-python` library. 
4. Implement robust `save_trajectory_record()` and `save_accepted_record()` functions that execute parameterized INSERT statements.
5. Wrap all database operations in try/except blocks to guarantee that a network timeout never crashes the LangGraph execution loop running in Person 1's environment.