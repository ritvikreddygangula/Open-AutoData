"""The Agentic Self-Instruct loop (Autodata paper Fig. 7) as a LangGraph StateGraph.

Run it: python -m src.agent_graph --limit 3
"""
import argparse
import importlib
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

from langgraph.graph import END, START, StateGraph

from src import config
from src.chunks import load_chunks
from src.nodes import node_challenger, node_evaluate, node_judge, node_solvers, node_verifier
from src.recorder import Recorder
from src.state import AgentState, initial_state

log = logging.getLogger(__name__)

# One round is at most 8 node steps; leave headroom so MAX_ROUNDS never trips LangGraph's limit.
RECURSION_LIMIT = 10 * config.MAX_ROUNDS + 10


def _next_unless_error(next_node: str):
    return lambda state: "evaluate" if state.get("error") else next_node


def after_verifier(state) -> str:
    return "evaluate" if state.get("error") or state.get("verifier_verdict") == "FAIL" else "weak_solvers"


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
    # Unlike the paper we always run the strong solver: every round then has a gap for the chart and demo.
    graph.add_conditional_edges("weak_judge", _next_unless_error("strong_solvers"), ["strong_solvers", "evaluate"])
    graph.add_conditional_edges("strong_solvers", _next_unless_error("strong_judge"), ["strong_judge", "evaluate"])
    graph.add_edge("strong_judge", "evaluate")
    graph.add_edge("evaluate", "record")
    graph.add_conditional_edges("record", after_record, ["challenger", END])
    return graph.compile()


def run_chunk(graph, chunk: dict, run_id: str) -> dict:
    state = initial_state(str(chunk["chunk_id"]), chunk["text"], run_id=run_id)
    return graph.invoke(state, {"recursion_limit": RECURSION_LIMIT})


def run(chunks: list[dict], run_id: str, recorder: Recorder, workers: int = 4) -> list[dict]:
    """Run chunks in parallel; a crash in one chunk is reported and never stops the others."""
    graph = build_graph(recorder)

    def one(chunk: dict) -> dict:
        chunk_id = str(chunk["chunk_id"])
        try:
            final = run_chunk(graph, chunk, run_id)
        except Exception as e:
            log.exception("chunk %s crashed", chunk_id)
            return {"chunk_id": chunk_id, "status": "CRASHED", "rounds": None, "fail_reason": f"{type(e).__name__}: {e}"}
        return {"chunk_id": chunk_id, "status": final["status"], "rounds": final["round_num"],
                "fail_reason": final.get("fail_reason")}

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(one, chunks))


def snowflake_sync():
    """Person 2's sync module when it is installed and configured, else None (stay local)."""
    try:
        module = importlib.import_module("src.snowflake_sync")
    except ImportError:
        return None
    return module if module.enabled() else None


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Run the OpenAutodata agent loop over SEC chunks.")
    parser.add_argument("--chunks", default=config.CHUNKS_PATH, help="chunks .json or .csv")
    parser.add_argument("--limit", type=int, help="only the first N chunks")
    parser.add_argument("--workers", type=int, default=4, help="chunks processed in parallel")
    parser.add_argument("--run-id", default=f"run-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}")
    parser.add_argument("--out-dir", type=Path, default=config.DATA_DIR)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one line per model call drowns the summary

    chunks = load_chunks(args.chunks)[: args.limit]
    recorder = Recorder(args.out_dir / config.TRAJECTORIES_PATH.name, args.out_dir / config.ACCEPTED_PATH.name,
                        sync=snowflake_sync())
    print(f"{args.run_id}: {len(chunks)} chunks, {args.workers} at a time")
    summary = run(chunks, args.run_id, recorder, workers=args.workers)
    for s in summary:
        print(f"{s['chunk_id']}: {s['status']} after {s['rounds']} rounds" + (f" ({s['fail_reason']})" if s["fail_reason"] else ""))
    accepted = sum(s["status"] == "ACCEPTED" for s in summary)
    print(f"{accepted}/{len(summary)} accepted")


if __name__ == "__main__":
    main()
