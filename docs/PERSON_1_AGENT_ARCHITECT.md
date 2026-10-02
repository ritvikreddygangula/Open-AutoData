# PERSON_1_AGENT_ARCHITECT.md

## Your Role
You are the LangGraph Architect. Your objective is to build the multi-agent graph orchestrating the Challenger, Solvers, and Judge. Leverage your existing experience building agentic workflows and LangGraph pipelines to structure the state transitions cleanly.

## Instructions for Claude Code
1. Read `MASTER_SPEC.md` for the acceptance thresholds and file paths.
2. Define a LangGraph `AgentState` containing the chunk ID, text, generated question, reference answer, solver answers, scores, and status.
3. Build the LLM routing logic using an OpenAI-compatible client pointing to OpenRouter/LiteLLM.
4. Implement the nodes: `node_challenger`, `node_solvers` (parallel if possible, or sequential), `node_judge`, and `node_evaluate` (which applies the math filter).
5. Implement conditional edges: if `status == ACCEPTED` or max rounds reached, route to `node_save_accepted` and end. Otherwise, route back to `node_challenger` with the judge's feedback.
6. Ensure the pipeline handles JSON parsing failures gracefully.