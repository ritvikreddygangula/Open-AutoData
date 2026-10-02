"""The Agentic Self-Instruct loop (Autodata paper Fig. 7) as a LangGraph StateGraph."""
from langgraph.graph import END, START, StateGraph

from src import config
from src.gate import weak_gate_failures
from src.nodes import node_challenger, node_evaluate, node_judge, node_solvers, node_verifier
from src.recorder import Recorder
from src.state import AgentState, initial_state

# One round is at most 8 node steps; leave headroom so MAX_ROUNDS never trips LangGraph's limit.
RECURSION_LIMIT = 10 * config.MAX_ROUNDS + 10


def _next_unless_error(next_node: str):
    return lambda state: "evaluate" if state.get("error") else next_node


def after_verifier(state) -> str:
    return "evaluate" if state.get("error") or state.get("verifier_verdict") == "FAIL" else "weak_solvers"


def after_weak_judge(state) -> str:
    # Paper's compute saving: the strong solver only runs if the weak solver passed its checks.
    if state.get("error") or weak_gate_failures(state["weak_attempt_scores"]):
        return "evaluate"
    return "strong_solvers"


def after_record(state) -> str:
    return "challenger" if state["status"] == "REVISE" else END


def build_graph(recorder: Recorder):
    def record(state) -> dict:
        recorder.save(state)  # every round is logged, accepted or not
        return {}

    graph = StateGraph(AgentState)
    graph.add_node("challenger", node_challenger)
    graph.add_node("verifier", node_verifier)
    graph.add_node("weak_solvers", lambda state: node_solvers(state, "weak"))
    graph.add_node("weak_judge", lambda state: node_judge(state, "weak"))
    graph.add_node("strong_solvers", lambda state: node_solvers(state, "strong"))
    graph.add_node("strong_judge", lambda state: node_judge(state, "strong"))
    graph.add_node("evaluate", node_evaluate)
    graph.add_node("record", record)

    graph.add_edge(START, "challenger")
    graph.add_conditional_edges("challenger", _next_unless_error("verifier"), ["verifier", "evaluate"])
    graph.add_conditional_edges("verifier", after_verifier, ["weak_solvers", "evaluate"])
    graph.add_conditional_edges("weak_solvers", _next_unless_error("weak_judge"), ["weak_judge", "evaluate"])
    graph.add_conditional_edges("weak_judge", after_weak_judge, ["strong_solvers", "evaluate"])
    graph.add_conditional_edges("strong_solvers", _next_unless_error("strong_judge"), ["strong_judge", "evaluate"])
    graph.add_edge("strong_judge", "evaluate")
    graph.add_edge("evaluate", "record")
    graph.add_conditional_edges("record", after_record, ["challenger", END])
    return graph.compile()


def run_chunk(graph, chunk: dict, run_id: str) -> dict:
    state = initial_state(str(chunk["chunk_id"]), chunk["text"], run_id=run_id)
    return graph.invoke(state, {"recursion_limit": RECURSION_LIMIT})
