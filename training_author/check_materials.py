"""Check the published PDF against its source and exact embedded starter files."""
from pathlib import Path
import hashlib
import io
import json
import zipfile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ATTACHMENT = "ABB_Workflow_Training_Starters.zip"


def material_files():
    root = ROOT / "training_kit"
    return {p.relative_to(root).as_posix(): p for p in root.rglob("*")
            if p.is_file() and not p.is_symlink() and "__pycache__" not in p.parts
            and ".pytest_cache" not in p.parts and ".auth" not in p.parts
            and p.suffix != ".pyc" and (not p.name.startswith(".env") or p.name == ".env.example")}


def main():
    pdf = PdfReader(ROOT / "docs/ABB_Workflow_Training.pdf")
    assert list(pdf.attachments) == [ATTACHMENT], "Expected one named starter attachment"
    data = pdf.attachments[ATTACHMENT]
    assert len(data) == 1, "Expected one starter ZIP"
    expected = material_files()
    with zipfile.ZipFile(io.BytesIO(data[0])) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == set(expected), "Embedded starter file list differs from source"
        for name, path in expected.items():
            assert archive.read(name) == path.read_bytes(), f"Stale embedded starter: {name}"
    guide = (ROOT / "training_author/guide.md").read_bytes()
    for lab in ("fw1", "fw2", "hw1", "hw2", "t1", "t2"):
        card = "\n".join(p for p in guide.decode().split("<!-- PAGE -->")
                         if p.strip().startswith("# " + lab.upper() + " "))
        assert (ROOT / f"training_kit/task_cards/{lab}.md").read_text() == card, f"Stale task card: {lab}"
    pages = [p for p in guide.decode().split("<!-- PAGE -->") if p.strip()]
    assert len(pdf.pages) == len(pages), "Logical page references have moved"
    assert pdf.metadata.get("/TrainingSourceSHA256") == hashlib.sha256(guide).hexdigest(), "PDF source is stale"
    assert pdf.metadata.get("/TrainingStartersSHA256") == hashlib.sha256(data[0]).hexdigest()
    manifest = json.loads((ROOT / "training_author/materials-manifest.json").read_text())
    assert manifest["guide_sha256"] == hashlib.sha256(guide).hexdigest()
    assert manifest["starters_sha256"] == hashlib.sha256(data[0]).hexdigest()
    assert manifest["files"] == {n: hashlib.sha256(p.read_bytes()).hexdigest() for n, p in sorted(expected.items())}
    assert min(manifest["page_scales"]) >= 0.75, "Page text shrunk below reviewed readability threshold"
    text = "\n".join(p.extract_text() for p in pdf.pages)
    for required in ("GitHub Copilot CLI", "stage1-fixtures", "append-only", "caller", "FW1", "HW2", "T2"):
        assert required in text, f"Missing published guidance: {required}"
    print(f"PDF/source/attachment verified: {len(pdf.pages)} pages, {len(expected)} exact starter files")


if __name__ == "__main__":
    main()
