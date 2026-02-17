"""
Global configurations for codebase.
"""
from pathlib import Path

# ----------------------------
# Path
# ----------------------------
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CLEAN_DIR = DATA_DIR / "clean"
RAW_DIR = DATA_DIR / "raw"