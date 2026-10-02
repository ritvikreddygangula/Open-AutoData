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

## feat/agent-nodes

- `3680f7b` Add verifier model and paper acceptance limits to config
- `0ae0225` Add rubric validation and weighted answer scoring
- `5c5a5b3` Add the paper's weak and strong acceptance checks
- `d6f1c1a` Extend agent state with challenger output, attempt scores and failure history
- `ac70ae3` Add default agent prompts adapted from the Autodata paper
- `048cee3` Add challenger node that writes context, question and rubric
- `d0d1eab` Add quality verifier node for leakage and rubric checks
- `fc9abaa` Add solver node that answers from context only
- `503588a` Add rubric judge node with code-computed scores
- `1bcc149` Add evaluate node applying the paper's acceptance gate
- `bbcf954` refactor: back off longer when an OpenRouter provider is rate-limited
- `5cb71c7` refactor: label a zero-scoring weak attempt as too hard instead of too easy
- `2261142` Update team docs with the paper-aligned agent design
