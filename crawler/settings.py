from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("TRF5_BASE_URL", "https://www5.trf5.jus.br")
REQUEST_TIMEOUT = int(os.getenv("TRF5_REQUEST_TIMEOUT", "30"))
DEFAULT_JSONL_PATH = Path(os.getenv("TRF5_OUTPUT_PATH", "data/processes.jsonl"))
DEFAULT_USER_AGENT = os.getenv(
    "TRF5_USER_AGENT",
    "cs-crowler-caixa-trf5/1.0 (requests; +https://www5.trf5.jus.br/cp/)",
)
