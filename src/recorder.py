"""Persist one record per round: local JSON files for the dashboard, Snowflake when configured."""
import json
import logging
import os
import threading
from pathlib import Path

from src.state import to_record

log = logging.getLogger(__name__)


class Recorder:
    def __init__(self, trajectories_path: Path, accepted_path: Path, sync=None):
        self.trajectories_path = Path(trajectories_path)
        self.accepted_path = Path(accepted_path)
        self.sync = sync  # src.snowflake_sync, or None to stay local
        self._lock = threading.Lock()  # chunks run in parallel threads

    def save(self, state) -> dict:
        record = to_record(state)
        accepted = record["status"] == "ACCEPTED"
        with self._lock:
            self._append(self.trajectories_path, record)
            if accepted:
                self._append(self.accepted_path, record)
        self._sync("save_trajectory_record", record)
        if accepted:
            self._sync("save_accepted_record", record)
        return record

    @staticmethod
    def _append(path: Path, record: dict) -> None:
        records = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        records.append(record)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Write then rename, so the dashboard polling this file never reads half a write.
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(records, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        os.replace(tmp, path)

    def _sync(self, method: str, record: dict) -> None:
        if self.sync is None:
            return
        try:
            getattr(self.sync, method)(record)
        except Exception as e:  # Snowflake must never stop the loop
            log.warning("Snowflake %s failed for chunk %s: %s", method, record["chunk_id"], e)
