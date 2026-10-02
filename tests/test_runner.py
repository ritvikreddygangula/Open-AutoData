import json
import sys
import types

from src import agent_graph
from src.recorder import Recorder


def test_one_crashing_chunk_does_not_stop_the_others(tmp_path, monkeypatch):
    def fake_run_chunk(graph, chunk, run_id):
        if chunk["chunk_id"] == "bad":
            raise KeyError("boom")
        return {"status": "ACCEPTED", "round_num": 2, "fail_reason": None}

    monkeypatch.setattr(agent_graph, "run_chunk", fake_run_chunk)
    recorder = Recorder(tmp_path / "t.json", tmp_path / "a.json")
    chunks = [{"chunk_id": "1", "text": "a"}, {"chunk_id": "bad", "text": "b"}, {"chunk_id": "3", "text": "c"}]
    summary = agent_graph.run(chunks, "run-1", recorder, workers=3)

    assert [s["chunk_id"] for s in summary] == ["1", "bad", "3"]
    assert [s["status"] for s in summary] == ["ACCEPTED", "CRASHED", "ACCEPTED"]
    assert summary[1]["fail_reason"] == "KeyError: 'boom'"
    assert summary[0]["rounds"] == 2


def test_snowflake_sync_is_used_only_when_enabled(monkeypatch):
    module = types.ModuleType("src.snowflake_sync")
    module.enabled = lambda: False
    monkeypatch.setitem(sys.modules, "src.snowflake_sync", module)
    assert agent_graph.snowflake_sync() is None
    module.enabled = lambda: True
    assert agent_graph.snowflake_sync() is module


def test_cli_runs_the_first_n_chunks_and_prints_a_summary(tmp_path, monkeypatch, capsys):
    chunks = tmp_path / "chunks.json"
    chunks.write_text(json.dumps([{"chunk_id": i, "text": f"text {i}"} for i in range(5)]))
    seen = {}

    def fake_run(chunk_list, run_id, recorder, workers):
        seen.update(ids=[c["chunk_id"] for c in chunk_list], run_id=run_id, workers=workers)
        return [{"chunk_id": c["chunk_id"], "status": "REJECTED", "rounds": 3, "fail_reason": "x"}
                for c in chunk_list]

    monkeypatch.setattr(agent_graph, "run", fake_run)
    monkeypatch.setattr(agent_graph, "snowflake_sync", lambda: None)
    agent_graph.main(["--chunks", str(chunks), "--limit", "2", "--workers", "2", "--run-id", "demo",
                      "--out-dir", str(tmp_path)])

    assert seen == {"ids": ["0", "1"], "run_id": "demo", "workers": 2}
    out = capsys.readouterr().out
    assert "0: REJECTED after 3 rounds (x)" in out and "0/2 accepted" in out


def test_cli_hides_per_request_http_logs(tmp_path, monkeypatch):
    import logging

    chunks = tmp_path / "chunks.json"
    chunks.write_text(json.dumps([{"chunk_id": 1, "text": "t"}]))
    monkeypatch.setattr(agent_graph, "run", lambda *args, **kwargs: [])
    monkeypatch.setattr(agent_graph, "snowflake_sync", lambda: None)
    agent_graph.main(["--chunks", str(chunks), "--out-dir", str(tmp_path)])
    assert logging.getLogger("httpx").level == logging.WARNING
