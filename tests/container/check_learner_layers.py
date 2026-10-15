"""Read a docker-save archive and reject assessment files in any learner layer."""
import json
from pathlib import Path
import sys
import tarfile

PREFIXES = ('opt/abb/materials/firmware/instructor/', 'opt/abb/materials/hardware/instructor/',
            'opt/abb/materials/hardware/tests/', 'opt/abb/materials/test_team/author_checks/',
            'opt/abb/repo/')


def check(archive: Path) -> None:
    with tarfile.open(archive) as outer:
        manifest = json.load(outer.extractfile('manifest.json'))
        leaked = []
        for layer in manifest[0]['Layers']:
            with tarfile.open(fileobj=outer.extractfile(layer), mode='r:*') as content:
                leaked.extend(member.name for member in content if member.isfile()
                              and member.name.lstrip('./').startswith(PREFIXES))
    if leaked:
        raise AssertionError('Assessment files in learner layers: '+', '.join(leaked))
    print('PASS: no assessment files in any learner image layer')


if __name__ == '__main__':
    check(Path(sys.argv[1]))
