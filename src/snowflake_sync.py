import json
import logging
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    import snowflake.connector
except ImportError:
    snowflake = None

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SCHEMA_SQL = ROOT / "sql" / "schema.sql"
FAILED_PATH = DATA_DIR / "snowflake_failed.jsonl"

TRAJECTORY_TABLE = "OPENAUTODATA_TRAJECTORIES"
ACCEPTED_TABLE = "OPENAUTODATA_ACCEPTED_SET"
CHUNKS_TABLE = "SOURCE_CHUNKS"

TRAJECTORY_COLS = [
    "RUN_ID", "ARM", "CHUNK_ID", "ROUND_NUM", "QUESTION", "REFERENCE_ANSWER",
    "WEAK_ANSWER", "STRONG_ANSWER", "WEAK_SCORE", "STRONG_SCORE", "SCORE_GAP",
    "JUDGE_FEEDBACK", "STATUS",
]
ACCEPTED_COLS = [
    "RUN_ID", "ARM", "CHUNK_ID", "ROUND_NUM", "QUESTION", "REFERENCE_ANSWER",
    "WEAK_SCORE", "STRONG_SCORE", "SCORE_GAP", "JUDGE_FEEDBACK", "STATUS",
]
NUMERIC_COLS = {"CHUNK_ID", "ROUND_NUM", "WEAK_SCORE", "STRONG_SCORE", "SCORE_GAP"}

log = logging.getLogger("snowflake_sync")
_conn = None


def _config():
    cfg = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
        "database": os.getenv("SNOWFLAKE_DATABASE", "OPENAUTODATA"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
        "login_timeout": 15,
        "network_timeout": 30,
    }
    if os.getenv("SNOWFLAKE_AUTHENTICATOR"):
        cfg["authenticator"] = os.getenv("SNOWFLAKE_AUTHENTICATOR")
    return cfg


def enabled():
    return (
        snowflake is not None
        and os.getenv("SNOWFLAKE_ENABLED", "1") != "0"
        and bool(os.getenv("SNOWFLAKE_ACCOUNT"))
        and bool(os.getenv("SNOWFLAKE_USER"))
    )


def _get_connection():
    global _conn
    if _conn is not None and not _conn.is_closed():
        return _conn
    _conn = snowflake.connector.connect(**_config())
    return _conn


def close():
    global _conn
    try:
        if _conn is not None:
            _conn.close()
    except Exception:
        pass
    _conn = None


def _execute(sql, params=None, fetch=False):
    global _conn
    if not enabled():
        return None
    for attempt in range(2):
        try:
            cur = _get_connection().cursor()
            try:
                cur.execute(sql, params)
                return cur.fetchall() if fetch else True
            finally:
                cur.close()
        except Exception as e:
            log.warning("Snowflake call failed (attempt %d): %s", attempt + 1, e)
            close()
    return None


def _to_float(value):
    try:
        return None if value is None or value == "" else float(value)
    except (TypeError, ValueError):
        return None


def _normalize(record):
    rec = dict(record)
    weak = _to_float(rec.get("weak_score"))
    strong = _to_float(rec.get("strong_score"))
    if rec.get("score_gap") is None and weak is not None and strong is not None:
        rec["score_gap"] = strong - weak
    rec.setdefault("arm", "loop")
    return rec


def _params(rec, cols):
    values = []
    for col in cols:
        value = rec.get(col.lower())
        if col in NUMERIC_COLS:
            value = _to_float(value)
        elif value is not None and not isinstance(value, str):
            value = json.dumps(value, default=str)
        values.append(value)
    values.append(json.dumps(rec, default=str))
    return values


def _backup(table, rec):
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with FAILED_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"table": table, "record": rec}, default=str) + "\n")
    except Exception as e:
        log.warning("Could not write backup record: %s", e)


def _insert(table, cols, record):
    try:
        rec = _normalize(record)
        placeholders = ", ".join(["%s"] * len(cols))
        sql = (
            f"INSERT INTO {table} ({', '.join(cols)}, RAW) "
            f"SELECT {placeholders}, PARSE_JSON(%s)"
        )
        ok = _execute(sql, _params(rec, cols))
        if not ok:
            _backup(table, rec)
            return False
        return True
    except Exception as e:
        log.warning("Insert into %s failed: %s", table, e)
        _backup(table, record)
        return False


def save_trajectory_record(record):
    return _insert(TRAJECTORY_TABLE, TRAJECTORY_COLS, record)


def save_accepted_record(record):
    return _insert(ACCEPTED_TABLE, ACCEPTED_COLS, record)


def create_tables():
    try:
        statements = [s.strip() for s in SCHEMA_SQL.read_text().split(";") if s.strip()]
    except Exception as e:
        log.warning("Could not read schema.sql: %s", e)
        return False
    return all(_execute(s) for s in statements)


def _load_local_chunks():
    for name in ("chunks.json", "source_chunks.jsonl", "source_chunks.csv"):
        path = DATA_DIR / name
        if not path.exists():
            continue
        try:
            if name.endswith(".jsonl"):
                return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
            if name.endswith(".json"):
                return json.loads(path.read_text(encoding="utf-8"))
            import csv
            with path.open(encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except Exception as e:
            log.warning("Could not read %s: %s", path, e)
    return []


def load_chunks(limit=None):
    sql = f"SELECT CHUNK_ID, SEC_DOCUMENT_ID, ADSH, CHUNK_TEXT FROM {CHUNKS_TABLE} ORDER BY CHUNK_ID"
    if limit:
        sql += f" LIMIT {int(limit)}"
    rows = _execute(sql, fetch=True)
    if rows:
        chunks = [
            {"chunk_id": int(r[0]), "sec_document_id": r[1], "adsh": r[2], "chunk_text": r[3]}
            for r in rows
        ]
    else:
        chunks = _load_local_chunks()
        for c in chunks:
            c["chunk_id"] = int(c["chunk_id"])
        if limit:
            chunks = chunks[: int(limit)]
    return chunks


def retry_failed():
    if not FAILED_PATH.exists():
        return 0
    try:
        lines = [json.loads(l) for l in FAILED_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    except Exception as e:
        log.warning("Could not read backup file: %s", e)
        return 0
    FAILED_PATH.unlink()
    sent = 0
    for item in lines:
        if item["table"] == TRAJECTORY_TABLE:
            ok = save_trajectory_record(item["record"])
        else:
            ok = save_accepted_record(item["record"])
        sent += int(ok)
    return sent


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Snowflake enabled:", enabled())
    print("Tables created:", create_tables())
    chunks = load_chunks()
    print("Chunks loaded:", len(chunks))
    test = {
        "run_id": "smoke_test", "arm": "test", "chunk_id": 0, "round_num": 0,
        "question": "test", "reference_answer": "test", "weak_score": 40,
        "strong_score": 90, "judge_feedback": "test", "status": "SMOKE_TEST",
    }
    print("Trajectory insert:", save_trajectory_record(test))
    _execute(f"DELETE FROM {TRAJECTORY_TABLE} WHERE RUN_ID = 'smoke_test'")
    close()
