"""Verify the virtual environment handbook, current cards and sanitized starter attachment."""
from pathlib import Path
import hashlib
import io
import json
import zipfile
from pypdf import PdfReader
from build_package import selected_files, starter_bytes

ROOT = Path(__file__).resolve().parents[1]
ATTACHMENT = "ABB_Workflow_Training_Starters.zip"


def main():
    pdf = PdfReader(ROOT / "docs/ABB_Workflow_Training.pdf")
    assert list(pdf.attachments) == [ATTACHMENT], "Expected one named starter attachment"
    items = pdf.attachments[ATTACHMENT]
    assert len(items) == 1
    data = items[0]
    assert data == starter_bytes(ROOT), "Embedded virtual environment starter differs from current clean source"
    expected = selected_files(ROOT, 'learner', include_pdf=False)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.testzip() is None
    guide = (ROOT / "training_author/guide.md").read_bytes()
    for lab in ("fw1", "fw2", "hw1", "hw2", "t1", "t2"):
        card = "\n".join(p for p in guide.decode().split("<!-- PAGE -->")
                         if p.strip().startswith("# " + lab.upper() + " "))
        assert (ROOT / f"training_kit/task_cards/{lab}.md").read_text() == card, f"Stale task card: {lab}"
    manifest = json.loads((ROOT / "training_author/materials-manifest.json").read_text())
    assert manifest['format_version'] == 2
    assert manifest['pages'] == len(pdf.pages)
    assert manifest['logical_sections'] == len([p for p in guide.decode().split('<!-- PAGE -->') if p.strip()])
    assert pdf.metadata.get('/TrainingSourceSHA256') == hashlib.sha256(guide).hexdigest()
    assert pdf.metadata.get('/TrainingStartersSHA256') == hashlib.sha256(data).hexdigest()
    assert manifest['guide_sha256'] == hashlib.sha256(guide).hexdigest()
    assert manifest['starters_sha256'] == hashlib.sha256(data).hexdigest()
    assert manifest['files'] == {n: hashlib.sha256(b).hexdigest() for n,b in sorted(expected.items())}
    assert manifest['layout'] == 'A4 flowing text; 9.5pt body; no shrink-to-fit'
    text = "\n".join(p.extract_text() for p in pdf.pages)
    for required in ('GitHub Copilot CLI', 'stage1-fixtures', 'append-only', 'caller', 'FW1', 'HW2', 'T2'):
        assert required in text, f"Missing published guidance: {required}"
    print(f"PDF/source/attachment verified: {len(pdf.pages)} pages, {len(expected)} exact starter files")


if __name__ == '__main__':
    main()
