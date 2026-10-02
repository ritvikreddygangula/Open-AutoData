import json
import threading
from types import SimpleNamespace

from src.recorder import Recorder
from tests.samples import ready_state


def read(path):
    return json.loads(path.read_text())


def make(tmp_path, sync=None):
    return Recorder(tmp_path / "trajectories.json", tmp_path / "accepted.json", sync=sync)


def test_every_round_goes_to_trajectories_and_only_accepted_to_accepted(tmp_path):
    recorder = make(tmp_path)
    recorder.save(ready_state(status="REVISE"))
    recorder.save(ready_state(round_num=2, status="ACCEPTED"))

    trajectories = read(tmp_path / "trajectories.json")
    assert [r["status"] for r in trajectories] == ["REVISE", "ACCEPTED"]
    accepted = read(tmp_path / "accepted.json")
    assert len(accepted) == 1 and accepted[0]["round_num"] == 2
    assert accepted[0]["context"] and accepted[0]["rubric"]


def test_appends_to_existing_files_across_runs(tmp_path):
    make(tmp_path).save(ready_state(status="REVISE"))
    make(tmp_path).save(ready_state(status="REVISE", run_id="run-2"))
    assert [r["run_id"] for r in read(tmp_path / "trajectories.json")] == ["run-1", "run-2"]


def test_concurrent_saves_all_survive(tmp_path):
    recorder = make(tmp_path)
    threads = [threading.Thread(target=recorder.save, args=(ready_state(chunk_id=str(i), status="REVISE"),))
               for i in range(20)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(int(r["chunk_id"]) for r in read(tmp_path / "trajectories.json")) == list(range(20))


def test_records_are_sent_to_snowflake_when_a_sync_module_is_given(tmp_path):
    sent = []
    sync = SimpleNamespace(save_trajectory_record=lambda r: sent.append(("traj", r["status"])),
                           save_accepted_record=lambda r: sent.append(("acc", r["status"])))
    recorder = make(tmp_path, sync=sync)
    recorder.save(ready_state(status="REVISE"))
    recorder.save(ready_state(status="ACCEPTED"))
    assert sent == [("traj", "REVISE"), ("traj", "ACCEPTED"), ("acc", "ACCEPTED")]


def test_snowflake_errors_never_stop_local_recording(tmp_path):
    def boom(record):
        raise RuntimeError("network down")

    recorder = make(tmp_path, sync=SimpleNamespace(save_trajectory_record=boom, save_accepted_record=boom))
    recorder.save(ready_state(status="ACCEPTED"))
    assert len(read(tmp_path / "accepted.json")) == 1
