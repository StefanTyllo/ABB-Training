"""One clean-material allowlist for virtual environments, distributions and PDF starters."""
from pathlib import Path
import shutil
import sys

EXCLUDED = {'.git', '.auth', '.codex', '.copilot', '.cache', '.npm', '.venv',
            '__pycache__', '.pytest_cache', 'node_modules', 'instructor', 'author_checks'}


def clean_material_files(root: Path):
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if path.is_symlink() or not path.is_file():
            continue
        if any(part in EXCLUDED or (part.startswith('.env') and part != '.env.example')
               for part in relative.parts):
            continue
        if relative.parts[:2] == ('hardware', 'tests'):
            continue
        if path.suffix.lower() in {'.zip', '.tar', '.gz', '.pyc'}:
            continue
        yield path


def copy_clean_materials(root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)
    for path in clean_material_files(root):
        destination = output/path.relative_to(root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)


if __name__ == '__main__':
    copy_clean_materials(Path(sys.argv[1]), Path(sys.argv[2]))
