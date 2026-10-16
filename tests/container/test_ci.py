from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS = ['validate-workflow-labs', 'copilot-smoke-test', 'refine-browser-feedback',
             'refine-fw1-replay', 'check-t1-package', 'check-t2-package']


@pytest.mark.parametrize('name', WORKFLOWS)
def test_workflow_uses_verified_shared_image_and_runtime_filters(name):
    import yaml
    workflow = yaml.load((ROOT/f'.github/workflows/{name}.yml').read_text(), Loader=yaml.BaseLoader)
    assert workflow['jobs']['image']['uses'] == './.github/workflows/build-training-image.yml'
    paths = workflow['on']['push']['paths']
    assert 'Dockerfile' in paths and 'docker/**' in paths
    jobs = [job for key, job in workflow['jobs'].items() if key != 'image']
    for job in jobs:
        assert 'image' in job['needs']
        steps = job['steps']
        assert not any('setup-node' in step.get('uses', '') or 'setup-python' in step.get('uses', '') for step in steps)
        assert any(step.get('uses', '').startswith('actions/download-artifact@') for step in steps)
        commands = '\n'.join(step.get('run', '') for step in steps)
        assert 'sha256sum -c training-image.tar.sha256' in commands
        assert 'docker load' in commands
        assert 'needs.image.outputs.image_id' in commands
        assert any(step.get('if') == 'always()' and step.get('uses', '').startswith('actions/upload-artifact@') for step in steps)


def test_lab_matrix_and_grade_remain_independent():
    import yaml
    workflow = yaml.load((ROOT/'.github/workflows/validate-workflow-labs.yml').read_text(), Loader=yaml.BaseLoader)
    job = workflow['jobs']['lab']
    assert workflow['on']['workflow_dispatch']['inputs']['lab']['options'] == ['all', 'fw1', 'fw2', 'hw1', 'hw2', 't1', 't2']
    expression = job['strategy']['matrix']['lab']
    assert "inputs.lab != 'all'" in expression
    assert '["fw1","fw2","hw1","hw2","t1","t2"]' in expression
    assert int(job['timeout-minutes']) == 80
    grade = next(s for s in job['steps'] if s.get('name') == 'Independent credential-free grading')
    assert grade['if'] == 'always()'
    assert '--network none' in grade['run']
    assert '/run/secrets' not in grade['run']
    assert 'COPILOT' not in grade.get('env', {})


def test_ci_wrapper_preserves_child_exit():
    result = subprocess.run([sys.executable, '/opt/abb/runtime/ci.py', '--',
                             sys.executable, '-c', 'raise SystemExit(7)'], capture_output=True, text=True)
    assert result.returncode == 7, result.stderr


def test_artifact_collection_excludes_state_and_retains_failed_evidence(tmp_path):
    sys.path.insert(0, '/opt/abb/runtime')
    from collect import collect_evidence
    root = tmp_path/'runs'
    (root/'t1/demo/.auth').mkdir(parents=True)
    (root/'t1/demo/evidence').mkdir()
    (root/'t1/demo/.auth/state.json').write_text('SYNTHETIC-STATE')
    (root/'t1/demo/.env').write_text('SYNTHETIC-TOKEN')
    (root/'t1/demo/evidence/failure.json').write_text('{"status":"FAIL"}')
    output = tmp_path/'retained'
    collect_evidence(root, output)
    assert (output/'t1/demo/evidence/failure.json').read_text() == '{"status":"FAIL"}'
    assert not (output/'t1/demo/.auth').exists()
    assert not (output/'t1/demo/.env').exists()


def test_empty_evidence_still_creates_collection_directory(tmp_path):
    sys.path.insert(0, '/opt/abb/runtime')
    from collect import collect_evidence
    root = tmp_path/'runs'
    root.mkdir()
    collect_evidence(root, tmp_path/'retained')
    assert (tmp_path/'retained').is_dir()


def test_shared_build_gates_offline_acceptance_before_image_export():
    import yaml
    workflow = yaml.load((ROOT/'.github/workflows/build-training-image.yml').read_text(), Loader=yaml.BaseLoader)
    steps = workflow['jobs']['build']['steps']
    gates = [index for index, step in enumerate(steps)
             if 'docker run' in step.get('run', '') and 'pytest' in step.get('run', '')]
    assert gates, 'Shared image build must run offline acceptance before paid rehearsals'
    export = next(index for index, step in enumerate(steps) if 'docker save' in step.get('run', ''))
    assert gates[0] < export
    assert '--network none' in steps[gates[0]]['run']
    assert not steps[gates[0]].get('env')
