#!/usr/bin/env python3
"""extract_inputs.py — docs/00-inputs/ の Office 原本（.docx / .xlsx / .pptx）を Markdown テキストにする。

出力：docs/01-rfp/extracted/<元ファイル名>.md（原本は変更しない。再実行で上書き）
- Word：見出しスタイルを # に、表を Markdown 表に、段落番号は本文のまま
- Excel：シートごとに使用範囲を Markdown 表に（結合セルは左上の値）
- PowerPoint：スライドごとにタイトル・本文・表・ノート
- .md / .txt はそのまま参照できるため対象外。PDF は Claude Code の Read で直接読む（--pdf で PyMuPDF があればテキスト化）
使い方（プロジェクトルートで）: bash .claude/skills/office-deliverables/scripts/build.sh extract
"""
from __future__ import annotations

import sys
from pathlib import Path

IN_DIR = Path("docs/00-inputs")
OUT_DIR = Path("docs/01-rfp/extracted")


def _cell(s) -> str:
    return ("" if s is None else str(s)).replace("|", "｜").replace("\r", "").replace("\n", "<br>").strip()


def _table_md(rows: list[list[str]]) -> list[str]:
    rows = [r for r in rows if any(c for c in r)]
    if not rows:
        return []
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * n]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return out + [""]


def docx_to_md(path: Path) -> str:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(path)
    lines = [f"# {path.name}（抽出テキスト）", ""]
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, doc)
            text = p.text.strip()
            if not text:
                continue
            style = (p.style.name if p.style is not None else "") or ""
            if style.startswith("Heading") or style.startswith("見出し"):
                digits = "".join(ch for ch in style if ch.isdigit()) or "1"
                lines += [f"{'#' * min(int(digits) + 1, 6)} {text}", ""]
            elif style == "Title":
                lines += [f"## {text}", ""]
            elif "List" in style:
                lines.append(f"- {text}")
            else:
                lines += [text, ""]
        elif tag == "tbl":
            t = Table(child, doc)
            rows = []
            for r in t.rows:
                cells, prev = [], None
                for c in r.cells:
                    cells.append("" if c._tc is prev else _cell(c.text))
                    prev = c._tc
                rows.append(cells)
            lines += [""] + _table_md(rows)
    return "\n".join(lines)


def xlsx_to_md(path: Path) -> str:
    from openpyxl import load_workbook

    wb = load_workbook(path, data_only=True)
    lines = [f"# {path.name}（抽出テキスト）", ""]
    for ws in wb.worksheets:
        lines += [f"## シート：{ws.title}", ""]
        rows = [[_cell(v) for v in r] for r in ws.iter_rows(values_only=True)]
        # 右端・下端の空列を落とす
        width = max((max((i + 1 for i, v in enumerate(r) if v), default=0) for r in rows), default=0)
        rows = [r[:width] for r in rows]
        lines += _table_md(rows) or ["（空のシート）", ""]
    return "\n".join(lines)


def pptx_to_md(path: Path) -> str:
    from pptx import Presentation

    prs = Presentation(path)
    lines = [f"# {path.name}（抽出テキスト）", ""]
    for i, s in enumerate(prs.slides, start=1):
        title = s.shapes.title.text_frame.text.strip() if s.shapes.title is not None and s.shapes.title.has_text_frame else ""
        lines += [f"## スライド {i}：{title}", ""]
        for sh in s.shapes:
            if sh == s.shapes.title:
                continue
            if sh.has_text_frame:
                for p in sh.text_frame.paragraphs:
                    t = "".join(r.text for r in p.runs).strip()
                    if t:
                        lines.append(("  " * p.level) + f"- {t}")
            if getattr(sh, "has_table", False) and sh.has_table:
                lines += [""] + _table_md([[_cell(c.text) for c in r.cells] for r in sh.table.rows])
        if s.has_notes_slide:
            note = s.notes_slide.notes_text_frame.text.strip()
            if note:
                lines += ["", f"> ノート：{note}"]
        lines.append("")
    return "\n".join(lines)


def pdf_to_md(path: Path) -> str | None:
    try:
        import pymupdf  # type: ignore
    except ImportError:
        return None
    d = pymupdf.open(path)
    lines = [f"# {path.name}（抽出テキスト）", ""]
    for i, page in enumerate(d, start=1):
        lines += [f"## p.{i}", "", page.get_text().strip(), ""]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") else Path(".")
    want_pdf = "--pdf" in argv
    src, out = root / IN_DIR, root / OUT_DIR
    if not src.is_dir():
        print(f"❌ {IN_DIR}/ がありません", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    conv = {".docx": docx_to_md, ".xlsx": xlsx_to_md, ".xlsm": xlsx_to_md, ".pptx": pptx_to_md}
    n = 0
    for p in sorted(src.rglob("*")):
        if not p.is_file() or p.name.startswith(("~$", ".")):
            continue
        fn = conv.get(p.suffix.lower())
        text = None
        if fn:
            try:
                text = fn(p)
            except Exception as e:  # noqa: BLE001
                print(f"⚠️  {p.relative_to(root)}：抽出失敗（{e}）")
                continue
        elif p.suffix.lower() == ".pdf" and want_pdf:
            text = pdf_to_md(p)
            if text is None:
                print(f"ℹ️  {p.name}：PyMuPDF が無いため省略（PDF は Read で直接読めます）")
                continue
        if text is None:
            continue
        rel = p.relative_to(src)
        dest = out / (str(rel).replace("/", "__") + ".md")
        dest.write_text(text + "\n", encoding="utf-8")
        n += 1
        print(f"✅ {p.relative_to(root)} → {dest.relative_to(root)}")
    if n == 0:
        print("ℹ️  抽出対象（.docx / .xlsx / .pptx）はありませんでした")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
