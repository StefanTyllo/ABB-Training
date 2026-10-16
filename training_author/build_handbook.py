"""Render the current Markdown and attach the same clean virtual environment starter context."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from markdown_it import MarkdownIt
from pypdf import PdfReader, PdfWriter
from build_package import starter_bytes, selected_files

STYLE = '''
body{font:9.5pt/1.30 Arial,sans-serif;color:#172337}h1{font-size:20pt;color:#174a70}
h2{font-size:14pt;color:#174a70}h3{font-size:11pt}h1,h2,h3{break-after:avoid}p:has(+pre){break-after:avoid}
.page+.page{break-before:page}pre{font:8pt/1.3 monospace;background:#eef3f7;padding:9px;
white-space:pre-wrap;overflow-wrap:anywhere;break-inside:avoid}code{font-size:9pt}
table{width:100%;border-collapse:collapse;font-size:8.5pt}th,td{border:1px solid #b8c7d3;
padding:5px;text-align:left;vertical-align:top}tr{break-inside:avoid}th{background:#e4edf5}
blockquote{border-left:3px solid #3283a8;margin-left:0;padding-left:12px;color:#294861}
a{color:#145c8a;overflow-wrap:anywhere}p,li{orphans:3;widows:3}
'''


def build_handbook(source: Path, output: Path, materials: Path) -> dict:
    source, output = source.resolve(strict=True), output.resolve()
    root = materials.resolve(strict=True).parent
    renderer = MarkdownIt('commonmark', {'html': True}).enable('table')
    sections = source.read_text().split('<!-- PAGE -->')
    html = '<!doctype html><meta charset="utf-8"><style>'+STYLE+'</style>'
    html += ''.join('<section class="page">'+renderer.render(part)+'</section>' for part in sections if part.strip())
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError('Choose a fresh handbook output path')
    starter = starter_bytes(root)
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    starter_hash = hashlib.sha256(starter).hexdigest()
    with tempfile.TemporaryDirectory(prefix='abb-handbook-') as directory:
        temp = Path(directory)
        (temp/'guide.html').write_text(html)
        subprocess.run(['node', str(Path(__file__).with_name('render_handbook.mjs')),
                        str(temp/'guide.html'), str(temp/'rendered.pdf')], check=True)
        reader = PdfReader(temp/'rendered.pdf')
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.add_metadata({'/Title':'ABB workflow training — virtual environment edition',
                             '/Subject':'Local Python virtual environment; live account acceptance is recorded separately',
                             '/TrainingSourceSHA256':source_hash,
                             '/TrainingStartersSHA256':starter_hash})
        writer.add_attachment('ABB_Workflow_Training_Starters.zip', starter)
        with output.open('xb') as stream:
            writer.write(stream)
    metadata = {'format_version': 2, 'pages': len(reader.pages),
                'logical_sections': len([part for part in sections if part.strip()]),
                'layout': 'A4 flowing text; 9.5pt body; no shrink-to-fit',
                'guide_sha256': source_hash, 'starters_sha256': starter_hash,
                'files': {name: hashlib.sha256(data).hexdigest() for name, data in
                          sorted(selected_files(root, 'learner', include_pdf=False).items())}}
    with output.with_name('materials-manifest.json').open('x') as stream:
        json.dump(metadata, stream, indent=2); stream.write('\n')
    return {'output': str(output), 'pages': len(reader.pages),
            'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'attachment_sha256': hashlib.sha256(starter).hexdigest(),
            'pdf_sha256': hashlib.sha256(output.read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--materials', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_handbook(args.source, args.output, args.materials), indent=2))
