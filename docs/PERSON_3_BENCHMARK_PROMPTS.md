# PERSON_3_BENCHMARK_PROMPTS.md

## Your Role
You are the Prompt Engineer & Benchmark Analyst. Your objective is to lock down the exact instructions for the agent models and build the evaluation script that proves this system beats standard generation.

## Instructions for Claude Code
1. Read `MASTER_SPEC.md` to understand the system flow.
2. Create `prompts.py` containing strict system instructions for:
   - The Challenger (must demand multi-step reasoning from the SEC text).
   - The Revision Agent (must ingest judge feedback to increase difficulty).
   - The Judge (must strictly grade 0-100 and output structured JSON).
3. Build `baseline.py` to generate standard, unverified single-shot questions from the raw chunks for comparison.
4. Build `benchmark.py` to run a blind head-to-head comparison (Baseline vs. OpenAutodata) using an independent model, and generate a matplotlib bar chart (`data/benchmark.png`) highlighting the difficulty score gap.