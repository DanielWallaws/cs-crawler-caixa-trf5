import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("TRF5_BASE_URL", "https://cp.trf5.jus.br")
REQUEST_TIMEOUT = int(os.getenv("TRF5_REQUEST_TIMEOUT", "30"))
SAVE_BATCH_SIZE = int(os.getenv("TRF5_SAVE_BATCH_SIZE", "25"))
DEFAULT_JSONL_PATH = Path(os.getenv("TRF5_OUTPUT_PATH", "data/processes.jsonl"))
USER_AGENT = os.getenv(
    "TRF5_USER_AGENT",
    "cs-crawler-caixa-trf5/1.0 (requests; +https://cp.trf5.jus.br/cp/)",
)

KNOWN_PROCESSES = [
    "0000881-39.2016.4.05.0000",
    "0013996-35.2011.4.05.8300",
    "0000007-41.2011.4.05.8403",
    "0009865-80.2014.4.05.0000",
    "0014481-40.2010.4.05.0000",
    "0005037-07.2013.4.05.8300",
]

KNOWN_CNPJS = [
    "34.020.354/0001-10",
]

KNOWN_PARTIES = [
    "CAIXA SEGURADORA",
]

PARTY_NAME_REQUIRED_TEXT = "S/A"
