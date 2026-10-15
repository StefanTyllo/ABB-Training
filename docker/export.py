"""Export work and evidence without authentication state or local caches."""
from pathlib import Path
import zipfile

EXCLUDED = {'.auth', '.codex', '.copilot', '.git', '.cache', '__pycache__',
            '.pytest_cache', 'node_modules', '.venv', 'auth.json', 'credentials.json',
            'tokens.json'}


def export_workspace(root: Path, output: Path) -> dict:
    root, output = root.resolve(strict=True), output.resolve()
    if output.is_relative_to(root):
        raise ValueError('Export destination must be outside the work directory')
    output.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(root.rglob('*')):
            relative = path.relative_to(root)
            if any(part in EXCLUDED or part.startswith('.env') for part in relative.parts):
                continue
            if path.is_symlink() or not path.is_file():
                continue
            archive.write(path, relative.as_posix())
            count += 1
    return {'status': 'PASS', 'output': str(output), 'files': count}
