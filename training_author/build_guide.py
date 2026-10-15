"""Build the handbook and exact starter attachment from reviewed source files.

Run: python training_author/build_guide.py
Dependencies: training_author/requirements.txt; DejaVu Sans/Mono system fonts.
Explicit PAGE markers preserve the handbook's existing logical page references.
"""
from pathlib import Path
import hashlib
import io
import json
import re
import zipfile

from markdown_it import MarkdownIt
from pypdf import PdfReader, PdfWriter
from reportlab import rl_config
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepInFrame, PageBreak, Paragraph, Preformatted, SimpleDocTemplate, Spacer,
    Table, TableStyle,
)

from check_materials import ATTACHMENT, ROOT, material_files

WIDTH, HEIGHT = A4
MARGIN = 34
AVAILABLE = WIDTH - 2 * MARGIN


def styles():
    fonts = Path("/usr/share/fonts/truetype/dejavu")
    for name, file in [("Body", "DejaVuSans.ttf"), ("Body-Bold", "DejaVuSans-Bold.ttf"),
                       ("Mono", "DejaVuSansMono.ttf")]:
        pdfmetrics.registerFont(TTFont(name, str(fonts / file)))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold",
                                 italic="Body", boldItalic="Body-Bold")
    base = ParagraphStyle("body", fontName="Body", fontSize=9.4, leading=12.0,
                          spaceAfter=5, alignment=TA_LEFT)
    return {
        "body": base,
        "quote": ParagraphStyle("quote", parent=base, leftIndent=10, borderPadding=5,
                                backColor=colors.HexColor("#eef4f8"), spaceBefore=3),
        "h1": ParagraphStyle("h1", parent=base, fontName="Body-Bold", fontSize=18,
                             leading=21, spaceAfter=10, textColor=colors.HexColor("#12334d")),
        "h2": ParagraphStyle("h2", parent=base, fontName="Body-Bold", fontSize=11.5,
                             leading=14, spaceBefore=7, spaceAfter=5),
        "h3": ParagraphStyle("h3", parent=base, fontName="Body-Bold", fontSize=10,
                             leading=12, spaceBefore=5),
        "cell": ParagraphStyle("cell", parent=base, fontSize=8.3, leading=10.4, spaceAfter=0),
        "code": ParagraphStyle("code", fontName="Mono", fontSize=7.5, leading=9.4,
                               leftIndent=5, rightIndent=5, spaceBefore=3, spaceAfter=7),
    }


def flowables(markdown, parser, sheet):
    tokens = parser.parse(markdown)
    result, lists = [], []
    prefix = ""
    quoted = 0

    def inline(token):
        html = parser.renderer.renderInline(token.children or [], parser.options, {})
        return html.replace("<code>", '<font name="Mono">').replace("</code>", "</font>")

    index = 0
    while index < len(tokens):
        token = tokens[index]
        if token.type == "heading_open":
            result.append(Paragraph(inline(tokens[index + 1]), sheet.get(token.tag, sheet["h3"])))
            index += 2
        elif token.type == "paragraph_open":
            style = sheet["quote"] if quoted else sheet["body"]
            result.append(Paragraph(prefix + inline(tokens[index + 1]), style))
            prefix = ""
            index += 2
        elif token.type == "fence":
            longest = max((len(line.expandtabs(4)) for line in token.content.splitlines()), default=1)
            size = min(7.5, (AVAILABLE - 12) / max(1, longest * 0.61))
            style = ParagraphStyle("code-fit", parent=sheet["code"], fontSize=size, leading=size * 1.24)
            result.append(Preformatted(token.content.rstrip(), style))
        elif token.type in ("bullet_list_open", "ordered_list_open"):
            lists.append(None if token.type == "bullet_list_open" else int(token.attrGet("start") or 1))
        elif token.type in ("bullet_list_close", "ordered_list_close"):
            lists.pop()
        elif token.type == "list_item_open":
            if lists[-1] is None:
                prefix = "• "
            else:
                prefix = str(lists[-1]) + ". "
                lists[-1] += 1
        elif token.type == "blockquote_open":
            quoted += 1
        elif token.type == "blockquote_close":
            quoted -= 1
        elif token.type == "table_open":
            rows, row = [], []
            index += 1
            while tokens[index].type != "table_close":
                item = tokens[index]
                if item.type == "tr_open":
                    row = []
                elif item.type == "inline":
                    row.append(Paragraph(inline(item), sheet["cell"]))
                elif item.type == "tr_close":
                    rows.append(row)
                index += 1
            columns = len(rows[0])
            weights = [max(12, min(65, max(len(re.sub('<[^>]+>', '', r[c].text)) for r in rows)))
                       for c in range(columns)]
            widths = [AVAILABLE * w / sum(weights) for w in weights]
            table = Table(rows, colWidths=widths, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e7eef3")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#b9c9d4")),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            result.extend([table, Spacer(1, 6)])
        index += 1
    return result


def main():
    rl_config.invariant = True
    guide = (ROOT / "training_author/guide.md").read_bytes()
    cards = ROOT / "training_kit/task_cards"
    cards.mkdir(exist_ok=True)
    for lab in ("fw1", "fw2", "hw1", "hw2", "t1", "t2"):
        card = "\n".join(p for p in guide.decode().split("<!-- PAGE -->")
                         if p.strip().startswith("# " + lab.upper() + " "))
        if not card:
            raise ValueError("Missing source task card: " + lab)
        (cards / f"{lab}.md").write_text(card)
    parser = MarkdownIt("commonmark").enable("table")
    sheet = styles()
    pages = [p for p in guide.decode().split("<!-- PAGE -->") if p.strip()]
    frames = [KeepInFrame(AVAILABLE, HEIGHT - 2 * MARGIN - 10,
                          flowables(page, parser, sheet), mode="shrink",
                          hAlign="LEFT", vAlign="TOP") for page in pages]
    story = []
    for index, frame in enumerate(frames):
        if index:
            story.append(PageBreak())
        story.append(frame)

    def footer(canvas, document):
        canvas.setFont("Body", 7)
        canvas.setFillColor(colors.HexColor("#526d80"))
        canvas.drawString(MARGIN, 17, "ABB workflow training | GitHub Copilot CLI")
        canvas.drawRightString(WIDTH - MARGIN, 17, str(document.page))

    rendered = io.BytesIO()
    document = SimpleDocTemplate(rendered, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                                 topMargin=MARGIN, bottomMargin=MARGIN,
                                 title="ABB Workflow Training", author="ABB training")
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    files = material_files()
    attachment = io.BytesIO()
    with zipfile.ZipFile(attachment, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, path in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    sha = lambda data: hashlib.sha256(data).hexdigest()
    source_hash, starter_hash = sha(guide), sha(attachment.getvalue())
    writer = PdfWriter()
    writer.append(PdfReader(rendered))
    writer.add_attachment(ATTACHMENT, attachment.getvalue())
    writer.add_metadata({"/Title": "ABB Workflow Training", "/Author": "ABB training",
                         "/TrainingSourceSHA256": source_hash,
                         "/TrainingStartersSHA256": starter_hash})
    destination = ROOT / "docs/ABB_Workflow_Training.pdf"
    with destination.open("wb") as stream:
        writer.write(stream)
    manifest = {"guide_sha256": source_hash, "starters_sha256": starter_hash,
                "pages": len(pages), "page_scales": [round(1 / getattr(f, "_scale", 1), 4) for f in frames],
                "files": {name: sha(path.read_bytes()) for name, path in sorted(files.items())}}
    (ROOT / "training_author/materials-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"Built {destination}: {len(pages)} logical pages, {len(files)} starter files")
    print("Page scales:", manifest["page_scales"])


if __name__ == "__main__":
    main()
