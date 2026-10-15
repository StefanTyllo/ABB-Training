from pathlib import Path
import importlib.util
import json
import subprocess
import sys
import zipfile
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[2]
LABS = ['fw1', 'fw2', 'hw1', 'hw2', 't1', 't2']


def package_builder():
    path = ROOT/'training_author/build_package.py'
    assert path.is_file(), 'Docker distribution builder is missing'
    sys.path.insert(0, str(path.parent))
    import build_package
    return build_package


def test_audience_packages_have_separate_allowlists(tmp_path):
    builder = package_builder()
    for audience in ['learner', 'facilitator']:
        result = builder.build_package(ROOT, tmp_path/audience, audience)
        with zipfile.ZipFile(result['archive']) as archive:
            names = archive.namelist()
            assert 'Dockerfile' in names and 'docker/runtime.lock.json' in names
            assert 'docs/ABB_Workflow_Training.pdf' in names
            assert 'release-manifest.json' in names
            assert all(f'docs/{lab.upper()}_STUDENT_GUIDE.md' in names for lab in LABS)
            assert not any('/.auth/' in n or '/.git/' in n or n.startswith(('runs/', 'work/')) for n in names)
            if audience == 'learner':
                assert not any('/instructor/' in n or '/author_checks/' in n or n.startswith(('validation_', 'training_ci/', 'training_author/')) for n in names)
                assert b'facilitator:' not in archive.read('compose.yaml')
            else:
                assert 'training_ci/grade_all.py' in names
                assert 'validation_t2_package/source_hashes.json' in names
            manifest = json.loads(archive.read('release-manifest.json'))
            assert manifest['audience'] == audience


def test_handbook_attachment_is_executable_and_clean(tmp_path):
    from pypdf import PdfReader
    reader = PdfReader(ROOT/'docs/ABB_Workflow_Training.pdf')
    assert list(reader.attachments) == ['ABB_Workflow_Training_Starters.zip']
    attachments = reader.attachments['ABB_Workflow_Training_Starters.zip']
    assert len(attachments) == 1
    import io
    with zipfile.ZipFile(io.BytesIO(attachments[0])) as archive:
        assert 'Dockerfile' in archive.namelist()
        assert not any('/instructor/' in n or '/author_checks/' in n or n.startswith('validation_') for n in archive.namelist())
        for name in archive.namelist():
            if name == 'release-manifest.json':
                continue
            current = ROOT/('compose.learner.yaml' if name == 'compose.yaml' else name)
            assert current.is_file(), 'Removed file remains in PDF starter: '+name
            assert archive.read(name) == current.read_bytes(), 'Stale PDF starter file: '+name
        archive.extractall(tmp_path/'attachment')
    for lab in LABS:
        for case in ['demo', 'transfer']:
            result = subprocess.run([sys.executable, str(tmp_path/'attachment/training_kit/prepare_lab.py'),
                                     lab, case, str(tmp_path/'work'/f'{lab}-{case}')],
                                    capture_output=True, text=True, timeout=30)
            assert result.returncode == 0, result.stderr


def test_package_excludes_synthetic_secrets_and_refuses_overwrite(tmp_path):
    import shutil
    builder = package_builder()
    source = tmp_path/'source'
    shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns('.git', '.superpowers', '__pycache__'))
    for path in [source, *source.rglob('*')]:
        if not path.is_symlink():
            path.chmod(path.stat().st_mode | 0o200)
    sentinel = 'PACKAGE_TEST_'+uuid.uuid4().hex
    (source/'training_kit/.env').write_text(sentinel)
    secret_dir = source/'training_kit/test_team/.auth'
    secret_dir.mkdir()
    (secret_dir/'state.json').write_text(sentinel)
    outside = tmp_path/'outside-secret'
    outside.write_text(sentinel)
    (source/'training_kit/leak').symlink_to(outside)
    for audience in ['learner', 'facilitator']:
        result = builder.build_package(source, tmp_path/audience, audience)
        original = Path(result['archive']).read_bytes()
        with zipfile.ZipFile(result['archive']) as archive:
            assert not any(sentinel.encode() in archive.read(name) for name in archive.namelist())
        with pytest.raises(FileExistsError):
            builder.build_package(source, tmp_path/audience, audience)
        assert Path(result['archive']).read_bytes() == original
        repeated = builder.build_package(source, tmp_path/(audience+'-repeat'), audience)
        assert Path(repeated['archive']).read_bytes() == original


@pytest.mark.parametrize('lab', LABS)
def test_each_exercise_has_usable_container_entry(lab):
    track = 'FIRMWARE' if lab.startswith('fw') else 'HARDWARE' if lab.startswith('hw') else 'TEST'
    for relative in [f'docs/{lab.upper()}_STUDENT_GUIDE.md', f'docs/{track}_TEAM_WALKTHROUGH.md',
                     'training_author/guide.md']:
        path = ROOT/relative
        assert path.is_file(), f'Missing current guide: {relative}'
        text = path.read_text()
        assert '**Host terminal**' in text and '**Inside the container**' in text
        assert 'docker compose up -d training' in text
        assert f'abb prepare {lab} demo' in text
        for suffix in ['demo', 'transfer-md', 'transfer-code']:
            location = f'/workspace/work/{lab}-{suffix}'
            assert f'docker compose exec --workdir {location} training bash' in text
            assert f'Expected: {location}' in text
        assert f'abb prepare {lab} transfer --name {lab}-transfer-md' in text
        assert f'abb prepare {lab} transfer --name {lab}-transfer-code' in text
        assert 'resume' in text.lower() and 'pwd' in text
        assert 'source .venv' not in text
