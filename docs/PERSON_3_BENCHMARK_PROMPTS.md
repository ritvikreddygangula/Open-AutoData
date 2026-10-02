# PERSON_3_BENCHMARK_PROMPTS.md

## Your Role
You are the Prompt Engineer & Benchmark Analyst. Your objective is to lock down the exact instructions for the agent models and build the evaluation script that proves this system beats standard generation.

## Instructions for Claude Code
1. Read `MASTER_SPEC.md` to understand the system flow, then the Autodata paper's Appendix C.1 (Figures 7-9): our agents follow its CS-research setup.
2. Create `src/prompts.py`. Any of these names you define overrides the fallback in `src/default_prompts.py` (read it first: it is a working starting point):
   - `CHALLENGER_SYSTEM`: write context + question + reference answer + 10-15 criterion rubric from the SEC chunk. Context must give the facts without leaking the answer; question must need multi-step reasoning, not recall. On later rounds the same prompt is reused; the user message lists earlier failures and asks for an entirely new question from a different angle, so there is **no separate revision prompt**.
   - `VERIFIER_SYSTEM`: the paper's quality verifier (leakage, recall vs. reasoning, rubric quality, type consistency).
   - `SOLVER_SYSTEM`: shared by weak and strong. Never hint at strength (the paper saw agents "cheat" by telling the weak solver to be weak).
   - `JUDGE_SYSTEM`: strict per-criterion grading, default to "not met" when in doubt.
3. **Keep the JSON output formats exactly as in `src/default_prompts.py`**; the nodes validate them (e.g. the judge must return `{"verdicts": [...], "note": "..."}` with one boolean per rubric criterion; rubric weights must be integers 1-7, no negative criteria).
4. Build `baseline.py` to generate standard, unverified single-shot questions from the raw chunks for comparison (the paper's "CoT Self-Instruct" baseline). Produce the same fields as the challenger (context, question, reference answer, rubric) so the comparison is fair, and set `arm="baseline"` on every record.
5. Build `benchmark.py` to run a blind head-to-head comparison (Baseline vs. OpenAutodata) using the independent final judge (`qwen/qwen3.8-2.4t-a95b`, `config.MODELS["final_judge"]`), and generate a matplotlib bar chart (`data/benchmark.png`) highlighting the difficulty score gap. The paper's Table 1 is a good template: weak avg, strong avg, gap, rounds per accepted item.
