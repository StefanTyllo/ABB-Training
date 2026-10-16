"""Build sanitized, reproducible virtual environment distributions from audience allowlists."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import zipfile
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"training_runtime"))
from material_manifest import clean_material_files

LABS = ['FW1', 'FW2', 'HW1', 'HW2', 'T1', 'T2']
RUNTIME_FILES = ['__init__.py', '__main__.py', 'paths.py', 'launcher.py', 'doctor.py',
                 'export.py', 'auth.py', 'ci.py', 'collect.py', 'material_manifest.py',
                 'package.json', 'package-lock.json', 'playwright.json', 'codex.toml', 'copilot-mcp.json']
EXCLUDED_PARTS = {'.git', '.superpowers', '.auth', '.codex', '.copilot', '.venv',
                  '__pycache__', '.pytest_cache', 'node_modules', '.cache'}


def safe(path: Path, root: Path) -> bool:
    relative = path.relative_to(root)
    if path.is_symlink() or not path.is_file():
        return False
    if any(part in EXCLUDED_PARTS or (part.startswith('.env') and part != '.env.example')
           for part in relative.parts):
        return False
    return path.suffix.lower() not in {'.zip', '.tar', '.gz', '.pyc'}


def selected_files(source: Path, audience: str, include_pdf: bool = True) -> dict[str, bytes]:
    source = source.resolve(strict=True)
    if audience not in {'learner', 'facilitator'}:
        raise ValueError('Unknown audience')
    required = ['pyproject.toml', 'setup_env.py', 'requirements.txt', 'requirements.lock',
                '.gitattributes', '.gitignore', 'README.md', 'COPILOT_ACTIONS_GUIDE.md']
    required += ['training_runtime/'+name for name in RUNTIME_FILES]
    required += [f'docs/{lab}_STUDENT_GUIDE.md' for lab in LABS]
    required += [f'docs/{track}_TEAM_WALKTHROUGH.md' for track in ['FIRMWARE','HARDWARE','TEST']]
    if include_pdf:
        required += ['docs/ABB_Workflow_Training.pdf']
    files = {}
    for relative in required:
        path = source/relative
        if not safe(path, source):
            raise ValueError('Required safe package input is missing: '+relative)
        files[relative] = path.read_bytes()
    for relative in ['docs/validation/virtual-environment.md']:
        if include_pdf and safe(source/relative, source):
            files[relative] = (source/relative).read_bytes()
    material_root = source/'training_kit'
    paths = clean_material_files(material_root) if audience == 'learner' else material_root.rglob('*')
    for path in paths:
        if safe(path, source):
            files[path.relative_to(source).as_posix()] = path.read_bytes()
    if audience == 'facilitator':
        for directory in ['training_ci', 'training_author', 'validation_browser', 'validation_replay',
                          'validation_t1_package', 'validation_t2_package', 'tests/runtime', '.github/workflows']:
            for path in (source/directory).rglob('*'):
                if safe(path, source):
                    files[path.relative_to(source).as_posix()] = path.read_bytes()
    return files


def manifest(files: dict[str, bytes], audience: str) -> dict:
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())}
    revision = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    return {'format_version': 1, 'audience': audience, 'revision': revision,
            'source_identity': 'content-sha256:'+revision,
            'runtime': {'python': '>=3.11', 'dependencies': 'requirements.lock', 'environment': '.venv'}, 'files': hashes}


def archive_bytes(files: dict[str, bytes], metadata: dict) -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        payload = dict(files)
        payload['release-manifest.json'] = (json.dumps(metadata, indent=2)+'\n').encode()
        for name, data in sorted(payload.items()):
            entry = zipfile.ZipInfo(name, date_time=(2026, 10, 15, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = (0o100755 if name.endswith('.sh') else 0o100644) << 16
            archive.writestr(entry, data)
    return output.getvalue()


def starter_bytes(source: Path) -> bytes:
    files = selected_files(source, 'learner', include_pdf=False)
    metadata = manifest(files, 'learner')
    metadata['handbook_attachment'] = True
    return archive_bytes(files, metadata)


def build_package(source: Path, output: Path, audience: str) -> dict:
    source, output = source.resolve(strict=True), output.resolve()
    if output.is_relative_to(source):
        raise ValueError('Package output must be outside the source tree')
    files = selected_files(source, audience)
    metadata = manifest(files, audience)
    name = 'abb-training'+('-facilitator' if audience == 'facilitator' else '')+'-'+metadata['revision'][:12]
    output.mkdir(parents=True, exist_ok=True)
    archive = output/(name+'.zip')
    data = archive_bytes(files, metadata)
    with archive.open('xb') as stream:
        stream.write(data)
    metadata['archive_sha256'] = hashlib.sha256(data).hexdigest()
    sidecar = output/(name+'.manifest.json')
    with sidecar.open('x') as stream:
        json.dump(metadata, stream, indent=2); stream.write('\n')
    return {'archive': str(archive), 'manifest': str(sidecar), 'sha256': metadata['archive_sha256']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--audience', choices=['learner','facilitator'], required=True)
    args = parser.parse_args()
    print(json.dumps(build_package(args.source, args.output, args.audience), indent=2))
