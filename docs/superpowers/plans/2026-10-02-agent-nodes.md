# Agent Nodes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the five Agentic Self-Instruct agents from the Autodata paper (§3.1, Appendix C.1) as LangGraph node functions: challenger, quality verifier, solvers, judge, evaluate.

**Architecture:** Each node is `node(state) -> dict` returning only the fields it changes. Pure logic (rubric validation/scoring, acceptance gate) lives in its own modules so nodes stay thin and the graph branch can reuse the gate for routing. Prompts come from Person 3's `src/prompts.py` when present, else `src/default_prompts.py`. No graph wiring here (`feat/agent-graph`).

**Tech Stack:** Python 3.13, langgraph 1.2, openai 3.x via OpenRouter, pytest.

**Spec:** Autodata paper (arXiv 2606.25996) §3.1, §4 (meta-optimised rubric rules), Appendix C.1 Figures 7–9; `docs/MASTER_SPEC.md`; revised handoff chain approved in chat 2026-10-02.

## Global Constraints

- Acceptance (paper Fig. 7 + MASTER_SPEC): weak avg `<= 65`, every weak attempt `<= 75` and `> 0`, strong avg `>= 60` and `< 95`, gap `>= 20`. Max `3` rounds.
- Paper shortcut: strong solver runs and is judged only if the weak gate passes.
- Solvers see only `context` + `question` (never the chunk or reference answer); weak and strong get the identical prompt; temperature `1.0`; `3` attempts each.
- Rubric: `10`–`15` criteria, positive integer weights `1`–`7` (paper §4). Judge returns met/not-met per criterion; code computes score = met weight / total weight × 100.
- Failed rounds feed the challenger every previous failed question grouped as TOO EASY / FAILED ON STRONG / FAILED QV and demand an entirely new question from a different angle.
- Infrastructure errors (LLMError, unusable JSON after the re-ask) end the chunk as `REJECTED` with `fail_reason="error: …"`; they are never fed back as question feedback.
- Prompt names shared with Person 3: `CHALLENGER_SYSTEM`, `VERIFIER_SYSTEM`, `SOLVER_SYSTEM`, `JUDGE_SYSTEM`.
- Never `git push`. One-line human commit messages.

## Review Focus

1. Challenger rubric with string weights (`"+5"`), weight 0 or 8, 9 or 16 criteria → rejected as invalid output, not silently clamped.
2. Judge returns a verdict list shorter/longer than the rubric, or `"yes"`/`"no"` strings → wrong length is an error; yes/no/true/false/1/0 are accepted.
3. Boundary scores exactly 65 / 75 / 60 / 95 / gap 20 → 65, 75, 60, gap 20 pass; strong 95 fails.
4. A weak attempt scoring 0 (paper "no zeros") → weak gate fails even if the average is low.
5. Concurrent solver/judge calls answered out of order → answers and scores stay matched to their attempt index.

---

## File Structure

| File | Responsibility |
|---|---|
| `src/config.py` | + `verifier` model, gate thresholds, rubric limits |
| `src/rubric.py` | `validate_rubric`, `parse_verdicts`, `score_answer` |
| `src/gate.py` | `weak_gate_failures`, `strong_gate_failures` |
| `src/state.py` | + challenger fields, attempt scores, verifier fields, `failure_mode`, `history`, `error` |
| `src/default_prompts.py` | Paper-derived system prompts, `get_prompt(name)` |
| `src/nodes.py` | `node_challenger`, `node_verifier`, `node_solvers(state, role)`, `node_judge(state, role)`, `node_evaluate` |
| `tests/fakes.py` | + `RoutedClient` answering per model, thread-safe |

## Tasks (each: failing test → run red → implement → run green → commit)

1. **Config** — `MODELS["verifier"]` (default judge model, `MODEL_VERIFIER` override), `WEAK_ATTEMPT_MAX=75`, `STRONG_MAX=95`, `RUBRIC_MIN_ITEMS=10`, `RUBRIC_MAX_ITEMS=15`, `RUBRIC_MAX_WEIGHT=7`. Commit: "Add verifier model and paper acceptance limits to config".
2. **Rubric** — `validate_rubric(raw) -> list[dict] | None` (`{"criterion": str, "weight": int}`; ints or digit strings 1–7 accepted, `"+5"`/floats/bools rejected); `parse_verdicts(raw, n) -> list[bool] | None`; `score_answer(rubric, verdicts) -> float` rounded to 1 dp. Commit: "Add rubric validation and weighted answer scoring".
3. **Gate** — `weak_gate_failures(scores) -> list[str]`, `strong_gate_failures(weak_avg, strong_scores) -> list[str]` with human-readable reasons. Commit: "Add the paper's weak and strong acceptance checks".
4. **State** — new fields; `to_record` adds `question_type`, `skill_tags`, `context`, `rubric`, `weak_attempt_scores`, `strong_attempt_scores`, `failure_mode` (land in Snowflake RAW). Commit: "Extend agent state with challenger output, attempt scores and failure history".
5. **Prompts** — four system prompts adapted from Figures 8–9 for SEC filings; `get_prompt` prefers `src.prompts`. Commit: "Add default agent prompts adapted from the Autodata paper".
6. **Challenger** — round 1 vs refinement message (grouped failure history); validates all six fields; increments `round_num`; clears per-round fields. Commit: "Add challenger node that writes context, question and rubric".
7. **Verifier** — four checks + feedback; PASS only if all four are good. Commit: "Add quality verifier node for leakage and rubric checks".
8. **Solvers** — `node_solvers(state, role)`, 3 parallel calls, order preserved. Commit: "Add solver node that answers from context only".
9. **Judge** — `node_judge(state, role)`, one parallel grading per answer, writes attempt scores, average, notes. Commit: "Add rubric judge node with code-computed scores".
10. **Evaluate** — error → REJECTED; QV fail → FAILED_QV; weak gate → TOO_EASY; strong ≥95 → TOO_EASY; strong low/gap small → FAILED_ON_STRONG; appends history; status by round. Commit: "Add evaluate node applying the paper's acceptance gate".
11. **Live smoke + changelog** — run one real chunk through the nodes by hand; append commits to `CHANGELOG.md`. Commit: "Update changelog for the agent nodes branch".
