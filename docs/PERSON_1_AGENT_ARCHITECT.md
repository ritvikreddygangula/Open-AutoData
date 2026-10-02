# PERSON_1_AGENT_ARCHITECT.md

## Your Role
You are the LangGraph Architect. Your objective is to build the multi-agent graph orchestrating the Challenger, Quality Verifier, Solvers, Judge and Evaluate step, following the Autodata paper's Agentic Self-Instruct loop (§3.1, Appendix C.1). See `MASTER_SPEC.md` §2-3 for the agents and the acceptance gate.

## Status
- **Done (`feat/agent-core`):** `src/config.py`, `src/chunks.py`, `src/state.py`, `src/llm.py` (OpenRouter client with retries and tolerant JSON parsing).
- **Done (`feat/agent-nodes`):** `src/rubric.py`, `src/gate.py`, `src/default_prompts.py`, and in `src/nodes.py`: `node_challenger`, `node_verifier`, `node_solvers(state, role)`, `node_judge(state, role)`, `node_evaluate`.
- **Next (`feat/agent-graph`):** `src/agent_graph.py`.

## Instructions for Claude Code (`feat/agent-graph`)
1. Read `MASTER_SPEC.md` for the agents, acceptance gate and record contract.
2. Wire the nodes in the paper's order: challenger -> verifier -> weak solvers -> judge(weak) -> [weak gate passes? strong solvers -> judge(strong)] -> evaluate. Use `src.gate.weak_gate_failures` to decide whether the strong solver runs.
3. Short-circuit to `node_evaluate` when `error` is set or the verifier returns `FAIL`.
4. After evaluate: `REVISE` loops back to the challenger; `ACCEPTED` saves to `data/accepted.json`; `REJECTED` ends the chunk.
5. Write every round's `to_record(state)` to `data/trajectories.json`, and call Person 2's `save_trajectory_record` / `save_accepted_record` when `src/snowflake_sync.py` is importable.
6. Generate one `run_id` per pipeline run; process several chunks in parallel (a chunk takes 3-8 minutes of model calls).
7. Settle the chunk shape with Person 2 (`text` + string `chunk_id` in `src/chunks.py` vs `chunk_text` + int `chunk_id` in their loader).
