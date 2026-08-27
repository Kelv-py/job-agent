"""
Central configuration. Loads secrets from .env (never commit .env itself).
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = BASE_DIR / "profile" / "profile_data.json"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

API_KEYS = []
for k, v in os.environ.items():
    if k.startswith("GEMINI_API_KEY") and v.strip():
        for key in v.split(','):
            key = key.strip()
            if key and key not in API_KEYS:
                API_KEYS.append(key)

if not API_KEYS:
    raise RuntimeError(
        "No GEMINI_API_KEYs found in .env. Please set GEMINI_API_KEY or GEMINI_API_KEY_1, etc."
    )

# Model choice: use a "pro"-tier model for the reasoning/tailoring steps
# (quality matters more than speed/cost here) and flash for quick extraction.
MODEL_REASONING = "gemini-3.5-flash"
MODEL_FAST = "gemini-3.5-flash"
