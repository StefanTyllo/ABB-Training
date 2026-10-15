"""Runtime output location; source and seed lookup remain repository-relative."""
import os
from pathlib import Path


def runs_root() -> Path:
    value = os.environ.get('ABB_RUNS_DIR')
    if value is None:
        return Path(__file__).resolve().parents[1] / 'runs'
    if not value.strip():
        raise ValueError('ABB_RUNS_DIR must not be empty')
    return Path(value)
