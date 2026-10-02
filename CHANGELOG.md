# Changelog

## feat/agent-core

- `c1aae4b` Set up Python project skeleton and agent core plan
- `47e48df` Add central config with model IDs and acceptance thresholds
- `2052cfa` Add chunk loader that cleans and converts the SEC CSV
- `2ebe1f4` Generate chunks.json from the Snowflake SEC export
- `eca8cfa` Add agent state and shared trajectory record contract
- `3e48a86` Add OpenRouter chat client with retries for flaky calls
- `e416e31` Add tolerant JSON parsing for model replies
- `2cf9806` refactor: let chat own retries and cap each OpenRouter request at 120s
- `cf78fa6` refactor: retry OpenRouter replies that come back without choices
- `c765338` refactor: keep scanning for JSON when the first brace block is not valid
- `5d8d7f4` refactor: make CSV loading portable to Windows and tolerant of stray columns
- `f5b4eab` refactor: tag every record with run_id and arm to match the Snowflake schema
- `a8f7ce8` refactor: include all three weak and strong answers in each trajectory record
