"""Repository-relative local runtime locations."""
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = Path(__file__).resolve().parent
WORK = (ROOT / 'work').resolve()
EXPORT = (ROOT / 'export').resolve()
NODE_MODULES = RUNTIME / 'node_modules'

def node_command():
    return shutil.which('node') or 'node'

def provider_command(provider):
    name = provider + ('.cmd' if os.name == 'nt' else '')
    local = NODE_MODULES / '.bin' / name
    return str(local) if local.is_file() else (shutil.which(provider) or provider)
