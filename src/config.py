"""Central configuration: model IDs, acceptance thresholds, data paths."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
# Per-request cap; reasoning models (judge, challenger) can take a while.
LLM_TIMEOUT_SECONDS = 120

MODELS = {
    "challenger": os.getenv("MODEL_CHALLENGER", "z-ai/glm-5.3"),
    "weak": os.getenv("MODEL_WEAK", "meta-llama/llama-3.2-3b-instruct"),
    "strong": os.getenv("MODEL_STRONG", "deepseek/deepseek-v4.1-flash"),
    "judge": os.getenv("MODEL_JUDGE", "nvidia/nemotron-3-super-120b-a12b"),
    "final_judge": os.getenv("MODEL_FINAL_JUDGE", "qwen/qwen3.8-2.4t-a95b"),
}

# Acceptance gate (MASTER_SPEC §2). Scores are 0-100.
WEAK_MAX = 65
STRONG_MIN = 60
GAP_MIN = 20
MAX_ROUNDS = 3
SOLVER_SAMPLES = 3

DATA_DIR = ROOT / "data"
CHUNKS_PATH = DATA_DIR / "chunks.json"
TRAJECTORIES_PATH = DATA_DIR / "trajectories.json"
ACCEPTED_PATH = DATA_DIR / "accepted.json"


class ConfigError(Exception):
    pass


def get_api_key() -> str:
    key = (os.getenv("OPEN_ROUTER") or "").strip()
    if not key:
        raise ConfigError("OPEN_ROUTER is not set; add it to .env")
    return key
