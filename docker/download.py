"""Build-only verified runtime downloads. No version resolution at build time."""
import hashlib
import json
from pathlib import Path
import tarfile
import tempfile
import urllib.request
import zipfile

lock = json.loads(Path('/opt/abb/runtime/runtime.lock.json').read_text())
with tempfile.TemporaryDirectory() as temp:
    for name, artifact in [('node', lock['node']), ('chrome', lock['chrome']['chrome']),
                           ('chromedriver', lock['chrome']['chromedriver'])]:
        archive = Path(temp) / name
        urllib.request.urlretrieve(artifact['url'], archive)
        actual = hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()
        if actual != artifact['sha256']:
            raise RuntimeError(f'{name}: checksum mismatch')
        if name == 'node':
            with tarfile.open(archive) as source:
                source.extractall(temp, filter='data')
            Path(temp, 'node-v22.23.3-linux-x64').rename('/opt/abb/node')
        else:
            with zipfile.ZipFile(archive) as source:
                source.extractall('/opt/abb/browser')
                for entry in source.infolist():
                    if entry.external_attr >> 16:
                        Path('/opt/abb/browser', entry.filename).chmod(entry.external_attr >> 16)
