"""pptx_builder.py — 要件定義サマリー（PowerPoint、16:9）を生成する。

入力は docs/04-deliverables/summary-deck.yaml（office-document-producer が書くスライド構成）。
無ければ docs/03-requirements/ から件数・主要 BZ/UC・未決 OQ を拾った既定構成で作る。

スライド型：title / agenda / section / bullets / kpi / table / two_column / steps / before_after / closing
各スライドに message（キーメッセージ＝結論 1 文）と notes（話者ノート）と source（出典）を付けられる。
"""
from __future__ import annotations

import math
from pathlib import Path

import yaml
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

import common
import mdparse as md
from profile import hex_to_rgb, out_name
from xlsx_builder import ExcelBuilder

W, H = Inches(13.333), Inches(7.5)
LM = Inches(0.6)
CW = W - 2 * LM
BODY_TOP = Inches(1.85)
BODY_BOTTOM = Inches(6.75)


def rgb(h: str) -> RGBColor:
    return RGBColor(*hex_to_rgb(h))


class DeckBuilder:
    def __init__(self, prof: dict, root: Path):
        self.prof, self.root, self.t = prof, root, prof["theme"]
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = W, H
        self.blank = self.prs.slide_layouts[6]
        self.font = self.t["font_ui"]
        self.page = 0
        self.total = 0
        self.warnings: list[str] = []
        self.max_rows = prof["powerpoint"].get("max_table_rows", 9)

    # ------------------------------------------------------------ primitives
    def _text(self, slide, x, y, w, h, text, size=18, bold=False, color=None, align=PP_ALIGN.LEFT,
              anchor=MSO_ANCHOR.TOP, font=None):
        tb = slide.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = Inches(0.05)
        tf.margin_top = tf.margin_bottom = Inches(0.03)
        lines = str(text).split("\n")
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.alignment = align
            r = p.add_run()
            r.text = line
            self._font(r, size, bold, color or "262626", font)
        return tb

    def _font(self, run, size, bold=False, color="262626", font=None):
        f = run.font
        f.size = Pt(size)
        f.bold = bold
        f.color.rgb = rgb(color)
        name = font or self.font
        f.name = name
        rpr = run._r.get_or_add_rPr()
        for tag in ("a:latin", "a:ea", "a:cs"):
            el = rpr.find(qn(tag))
            if el is None:
                el = rpr.makeelement(qn(tag), {})
                rpr.append(el)
            el.set("typeface", name)

    def _rect(self, slide, x, y, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
        s = slide.shapes.add_shape(shape, x, y, w, h)
        s.fill.solid()
        s.fill.fore_color.rgb = rgb(fill)
        if line:
            s.line.color.rgb = rgb(line)
            s.line.width = Pt(0.75)
        else:
            s.line.fill.background()
        s.shadow.inherit = False
        return s

    def _fit(self, texts: list[tuple[int, str]], box_w, box_h, start=18, minimum=11) -> int:
        """(インデント段, 文字列) の並びが箱に収まる最大フォントサイズを概算する。"""
        for size in range(start, minimum - 1, -1):
            char_w = size / 72 * 0.52  # 半角 1 文字の幅（インチ）
            lines = 0
            for depth, s in texts:
                avail = (box_w / 914400) - 0.35 - 0.3 * depth
                per_line = max(1, int(avail / char_w))
                lines += max(1, math.ceil(common.text_width(s) / per_line))
            height = lines * size / 72 * 1.35 + len(texts) * size / 72 * 0.35
            if height <= box_h / 914400:
                return size
        self.warnings.append(f"スライド {self.page}: 本文が多く最小 {minimum}pt でも収まらない可能性")
        return minimum

    def _notes(self, slide, spec):
        notes = spec.get("notes")
        src = spec.get("source_note") or (spec.get("source") if isinstance(spec.get("source"), str) else None)
        text = "\n".join(x for x in [notes, f"出典：{src}" if src else None] if x)
        if text:
            slide.notes_slide.notes_text_frame.text = text

    def _frame(self, spec) -> object:
        """タイトル・キーメッセージ・フッターを持つ通常スライド。"""
        s = self.prs.slides.add_slide(self.blank)
        self.page += 1
        self._rect(s, 0, 0, W, Inches(0.12), self.t["primary"])
        self._text(s, LM, Inches(0.35), CW, Inches(0.7), spec.get("title", ""), 26, True, self.t["primary"],
                   anchor=MSO_ANCHOR.MIDDLE)
        msg = spec.get("message")
        line_y = Inches(1.1)
        self._rect(s, LM, line_y, CW, Emu(19050), self.t["accent"])
        if msg:
            self._text(s, LM, Inches(1.2), CW, Inches(0.55), msg, 16, True, self.t["accent"], anchor=MSO_ANCHOR.MIDDLE)
        p = self.prof["project"]
        self._text(s, LM, Inches(7.0), Inches(8), Inches(0.35), f"{p['name']}｜{self.prof['powerpoint']['kind']}　{p['confidentiality']}",
                   9, False, self.t["muted"], anchor=MSO_ANCHOR.MIDDLE)
        self._text(s, W - LM - Inches(2), Inches(7.0), Inches(2), Inches(0.35), f"{self.page}", 10, True, self.t["muted"],
                   align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE)
        self._notes(s, spec)
        return s

    # ------------------------------------------------------------ slide types
    def title(self, spec):
        s = self.prs.slides.add_slide(self.blank)
        self.page += 1
        p = self.prof["project"]
        self._rect(s, 0, 0, Inches(0.35), H, self.t["primary"])
        self._rect(s, Inches(0.35), 0, Inches(0.08), H, self.t["accent"])
        if p.get("client") and not p["client"].startswith("（"):
            self._text(s, Inches(1.1), Inches(1.4), Inches(11), Inches(0.5), f"{p['client']}　御中", 18, False, self.t["muted"])
        self._text(s, Inches(1.1), Inches(2.1), Inches(11.5), Inches(0.7), spec.get("project") or p["name"], 24, True, self.t["muted"])
        self._text(s, Inches(1.1), Inches(2.8), Inches(11.5), Inches(1.3), spec.get("title") or self.prof["powerpoint"]["kind"], 40, True,
                   self.t["primary"], anchor=MSO_ANCHOR.MIDDLE)
        if spec.get("subtitle"):
            self._text(s, Inches(1.1), Inches(4.1), Inches(11.5), Inches(0.6), spec["subtitle"], 18, False, "404040")
        self._rect(s, Inches(1.1), Inches(4.85), Inches(5.5), Emu(25400), self.t["accent"])
        meta = f"第 {p['version']} 版　{p['date']}\n{p['vendor']}"
        self._text(s, Inches(1.1), Inches(5.05), Inches(8), Inches(0.9), meta, 14, False, "404040")
        self._text(s, W - Inches(3.1), Inches(6.85), Inches(2.6), Inches(0.4), p["confidentiality"], 11, True, "C00000",
                   align=PP_ALIGN.RIGHT)
        self._notes(s, spec)

    def section(self, spec):
        s = self.prs.slides.add_slide(self.blank)
        self.page += 1
        bg = s.background.fill
        bg.solid()
        bg.fore_color.rgb = rgb(self.t["primary"])
        self._rect(s, LM, Inches(3.55), Inches(1.2), Emu(38100), "FFFFFF")
        if spec.get("number"):
            self._text(s, LM, Inches(2.2), Inches(4), Inches(1.0), str(spec["number"]), 44, True, self.t["light"])
        self._text(s, LM, Inches(3.75), Inches(12), Inches(1.0), spec.get("title", ""), 34, True, "FFFFFF")
        if spec.get("message"):
            self._text(s, LM, Inches(4.75), Inches(12), Inches(0.8), spec["message"], 16, False, self.t["light"])
        self._notes(s, spec)

    def agenda(self, spec, sections):
        s = self._frame({**spec, "title": spec.get("title", "本日のご説明内容")})
        y = BODY_TOP
        step = min(Inches(0.75), (BODY_BOTTOM - BODY_TOP) // max(len(sections), 1))
        for i, sec in enumerate(sections, start=1):
            self._rect(s, LM + Inches(0.4), y + Inches(0.08), Inches(0.5), Inches(0.5), self.t["primary"], shape=MSO_SHAPE.OVAL)
            self._text(s, LM + Inches(0.4), y + Inches(0.08), Inches(0.5), Inches(0.5), str(i), 16, True, "FFFFFF",
                       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
            self._text(s, LM + Inches(1.15), y, Inches(10.5), Inches(0.66), sec, 20, False, "262626", anchor=MSO_ANCHOR.MIDDLE)
            y += step

    def _bullet_box(self, s, x, y, w, h, bullets, start=18):
        items: list[tuple[int, str, bool]] = []

        def walk(bs, depth):
            for b in bs or []:
                if isinstance(b, dict):
                    items.append((depth, str(b.get("text", "")), bool(b.get("bold"))))
                    walk(b.get("children"), depth + 1)
                else:
                    items.append((depth, str(b), False))

        walk(bullets, 0)
        size = self._fit([(d, t) for d, t, _ in items], w, h, start)
        tb = s.shapes.add_textbox(x, y, w, h)
        tf = tb.text_frame
        tf.word_wrap = True
        for i, (depth, text, bold) in enumerate(items):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(size * 0.45)
            p.level = min(depth, 4)
            mark = "■ " if depth == 0 else "・"
            r = p.add_run()
            r.text = mark
            self._font(r, size * (0.7 if depth == 0 else 1), False, self.t["accent"])
            r = p.add_run()
            r.text = text
            self._font(r, size - 2 * depth, bold, "262626")
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(int(Inches(0.3 + 0.35 * depth))))
            pPr.set("indent", str(int(-Inches(0.3))))
        return tb

    def bullets(self, spec):
        s = self._frame(spec)
        self._bullet_box(s, LM, BODY_TOP, CW, BODY_BOTTOM - BODY_TOP, spec.get("bullets"))

    def two_column(self, spec):
        s = self._frame(spec)
        gap = Inches(0.4)
        cw = (CW - gap) // 2
        for i, side in enumerate(("left", "right")):
            col = spec.get(side) or {}
            x = LM + i * (cw + gap)
            y = BODY_TOP
            if col.get("heading"):
                self._rect(s, x, y, cw, Inches(0.5), self.t["primary"] if i == 0 else self.t["accent"])
                self._text(s, x, y, cw, Inches(0.5), col["heading"], 16, True, "FFFFFF", PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
                y += Inches(0.65)
            self._bullet_box(s, x, y, cw, BODY_BOTTOM - y, col.get("bullets"), 16)

    def before_after(self, spec):
        spec = {**spec,
                "left": {"heading": spec.get("before_heading", "現状（Before）"), "bullets": spec.get("before")},
                "right": {"heading": spec.get("after_heading", "実現後（After）"), "bullets": spec.get("after")}}
        s = self._frame(spec)
        gap = Inches(0.9)
        cw = (CW - gap) // 2
        for i, side in enumerate(("left", "right")):
            col = spec[side]
            x = LM + i * (cw + gap)
            color = "7F7F7F" if i == 0 else self.t["primary"]
            self._rect(s, x, BODY_TOP, cw, Inches(0.5), color)
            self._text(s, x, BODY_TOP, cw, Inches(0.5), col["heading"], 16, True, "FFFFFF", PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE)
            box = self._rect(s, x, BODY_TOP + Inches(0.5), cw, BODY_BOTTOM - BODY_TOP - Inches(0.5), "FFFFFF", line=color)
            self._bullet_box(s, x + Inches(0.15), BODY_TOP + Inches(0.65), cw - Inches(0.3), BODY_BOTTOM - BODY_TOP - Inches(0.8), col["bullets"], 16)
        arrow = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, LM + cw + Inches(0.15), BODY_TOP + Inches(2.0), Inches(0.6), Inches(0.8))
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = rgb(self.t["accent"])
        arrow.line.fill.background()

    def kpi(self, spec):
        s = self._frame(spec)
        items = spec.get("items") or []
        n = max(1, len(items))
        per_row = n if n <= 4 else math.ceil(n / 2)
        rows = math.ceil(n / per_row)
        gap = Inches(0.3)
        cw = (CW - gap * (per_row - 1)) // per_row
        ch = min(Inches(2.3), (BODY_BOTTOM - BODY_TOP - gap * (rows - 1)) // rows)
        for i, it in enumerate(items):
            r, c = divmod(i, per_row)
            x = LM + c * (cw + gap)
            y = BODY_TOP + r * (ch + gap)
            self._rect(s, x, y, cw, ch, self.t["light"])
            self._rect(s, x, y, Inches(0.09), ch, self.t["primary"])
            self._text(s, x + Inches(0.2), y + Inches(0.12), cw - Inches(0.3), Inches(0.45), str(it.get("label", "")), 14, True, self.t["primary"])
            self._text(s, x + Inches(0.2), y + Inches(0.55), cw - Inches(0.3), Inches(1.0), str(it.get("value", "")), 40, True, "262626",
                       anchor=MSO_ANCHOR.MIDDLE)
            if it.get("sub"):
                self._text(s, x + Inches(0.2), y + ch - Inches(0.6), cw - Inches(0.3), Inches(0.5), str(it["sub"]), 11, False, self.t["muted"])

    def steps(self, spec):
        s = self._frame(spec)
        steps = spec.get("steps") or []
        n = max(1, len(steps))
        gap = Inches(0.15)
        cw = (CW - gap * (n - 1)) // n
        for i, st in enumerate(steps):
            x = LM + i * (cw + gap)
            chev = s.shapes.add_shape(MSO_SHAPE.CHEVRON if i else MSO_SHAPE.PENTAGON, x, BODY_TOP, cw, Inches(0.8))
            chev.fill.solid()
            chev.fill.fore_color.rgb = rgb(self.t["primary"] if st.get("current") or i == spec.get("current", -1) else self.t["accent"])
            chev.line.fill.background()
            tf = chev.text_frame
            tf.text = ""
            r = tf.paragraphs[0].add_run()
            r.text = str(st.get("label", ""))
            tf.paragraphs[0].alignment = PP_ALIGN.CENTER
            self._font(r, 14, True, "FFFFFF")
            if st.get("period"):
                self._text(s, x, BODY_TOP + Inches(0.9), cw, Inches(0.4), str(st["period"]), 12, True, self.t["accent"], PP_ALIGN.CENTER)
            self._bullet_box(s, x, BODY_TOP + Inches(1.35), cw, BODY_BOTTOM - BODY_TOP - Inches(1.35), st.get("bullets") or [st.get("text", "")], 14)

    def table(self, spec, sources):
        columns, rows = self._table_data(spec, sources)
        if not columns:
            self.warnings.append(f"表スライド「{spec.get('title')}」のデータが空")
            return
        chunks = [rows[i:i + self.max_rows] for i in range(0, len(rows), self.max_rows)] or [[]]
        for ci, chunk in enumerate(chunks):
            title = spec.get("title", "") + (f"（{ci + 1}/{len(chunks)}）" if len(chunks) > 1 else "")
            s = self._frame({**spec, "title": title})
            ncol = len(columns)
            size = 12 if ncol <= 5 else (11 if ncol <= 7 else 10)
            weights = common.col_weights(columns, chunk, min_w=4, max_w=40)
            total = sum(weights)
            row_h = Inches(0.42)
            height = row_h * (len(chunk) + 1)
            shape = s.shapes.add_table(len(chunk) + 1, ncol, LM, BODY_TOP, CW, min(height, BODY_BOTTOM - BODY_TOP))
            tbl = shape.table
            # 既定テーブルスタイルの縞を無効にして自前で塗る
            tblPr = shape._element.graphic.graphicData.tbl.tblPr
            tblPr.set("bandRow", "0")
            tblPr.set("firstRow", "1")
            widths = [int(CW * w / total) for w in weights]
            floors = [int(Pt(f * size * 0.6 + 12)) for f in common.col_floors(columns, chunk)]
            if sum(floors) < CW:
                short = [i for i in range(ncol) if widths[i] < floors[i]]
                need = sum(floors[i] - widths[i] for i in short)
                rest = [i for i in range(ncol) if i not in short and widths[i] > floors[i]]
                pool = sum(widths[i] - floors[i] for i in rest)
                for i in short:
                    widths[i] = floors[i]
                for i in rest:
                    if pool > 0:
                        widths[i] -= int(need * (widths[i] - floors[i]) / pool)
            for i, w in enumerate(widths):
                tbl.columns[i].width = w
            for r in range(len(chunk) + 1):
                tbl.rows[r].height = row_h
                for c in range(ncol):
                    cell = tbl.cell(r, c)
                    cell.margin_left = cell.margin_right = Inches(0.06)
                    cell.margin_top = cell.margin_bottom = Inches(0.03)
                    cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                    text = columns[c] if r == 0 else (chunk[r - 1][c] if c < len(chunk[r - 1]) else "")
                    cell.text = ""
                    para = cell.text_frame.paragraphs[0]
                    run = para.add_run()
                    run.text = str(text).replace("<br>", "\n")
                    cell.fill.solid()
                    if r == 0:
                        cell.fill.fore_color.rgb = rgb(self.t["primary"])
                        self._font(run, size, True, "FFFFFF")
                        para.alignment = PP_ALIGN.CENTER
                    else:
                        cell.fill.fore_color.rgb = rgb("F5F8FC" if r % 2 == 0 else "FFFFFF")
                        self._font(run, size, c == 0, self.t["primary"] if c == 0 else "262626")

    def _table_data(self, spec, sources):
        if spec.get("columns") and spec.get("rows") is not None:
            return [str(c) for c in spec["columns"]], [[str(x) for x in r] for r in spec["rows"]]
        src = spec.get("from")
        if not src:
            return [], []
        blocks = sources.get(src.get("file", ""))
        if not blocks:
            return [], []
        header, rows = ExcelBuilder.collect(blocks, src)
        want = src.get("columns") or header
        idx = []
        for w in want:
            hit = next((i for i, h in enumerate(header) if h == w), None)
            if hit is None:
                hit = next((i for i, h in enumerate(header) if w in h), None)
            if hit is not None:
                idx.append(hit)
        if len(idx) < min(2, len(want)):
            idx = list(range(min(len(header), 5)))  # 指定列が見つからなければ先頭列で代替
        flt = src.get("filter") or {}
        if flt:
            col = next((i for i, h in enumerate(header) if flt.get("column", "") in h), None)
            if col is not None:
                vals = flt.get("in") or [flt.get("equals")]
                rows = [r for r in rows if any(str(r[col]).strip().startswith(str(v)) for v in vals if v)]
        if src.get("limit"):
            rows = rows[: int(src["limit"])]
        return [header[i] for i in idx], [[r[i] for i in idx] for r in rows]

    def closing(self, spec):
        s = self._frame({**spec, "title": spec.get("title", "今後の進め方")})
        if spec.get("bullets"):
            self._bullet_box(s, LM, BODY_TOP, CW, Inches(3.2), spec["bullets"])
        if spec.get("contact"):
            self._rect(s, LM, Inches(5.4), CW, Inches(1.2), self.t["light"])
            self._text(s, LM + Inches(0.3), Inches(5.5), CW - Inches(0.6), Inches(1.0), spec["contact"], 14, False, "262626",
                       anchor=MSO_ANCHOR.MIDDLE)

    # ------------------------------------------------------------ assemble
    def build(self, spec: dict, sources: dict, out_dir: Path) -> Path:
        slides = spec.get("slides") or []
        sections = [x.get("title", "") for x in slides if x.get("type") == "section"]
        self.title({k: v for k, v in spec.items() if k != "slides"})
        if spec.get("agenda", True) and len(sections) >= 2:
            self.agenda({}, sections)
        n = 0
        for sl in slides:
            t = sl.get("type", "bullets")
            if t == "section":
                n += 1
                sl = {"number": f"{n:02d}", **sl}
                self.section(sl)
            elif t == "table":
                self.table(sl, sources)
            elif hasattr(self, t) and t not in ("build", "title", "agenda"):
                getattr(self, t)(sl)
            else:
                self.warnings.append(f"未知のスライド型 {t}（bullets として描画）")
                self.bullets(sl)
        p = self.prof["project"]
        cp = self.prs.core_properties
        cp.title = f"{spec.get('title') or self.prof['powerpoint']['kind']}｜{p['name']}"
        cp.author = p.get("author") or p["vendor"]
        cp.subject = p["name"]
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / out_name(self.prof, self.prof["powerpoint"]["kind"], "pptx")
        self.prs.save(path)
        return path


# ---------------------------------------------------------------- default deck

def default_spec(prof: dict, sources: dict) -> dict:
    """summary-deck.yaml が無いときの既定構成（件数・主要 BZ / UC・未決 OQ）。"""
    def count(file, prefix, col=None, val=None):
        blocks = sources.get(file)
        if not blocks:
            return 0, ""
        h, rows = ExcelBuilder.collect(blocks, {"id_prefix": prefix})
        sub = ""
        if col:
            ci = next((i for i, x in enumerate(h) if col in x), None)
            if ci is not None:
                vals = [str(r[ci]).strip() for r in rows]
                if val:
                    return sum(v.startswith(val) for v in vals), ""
                tally = {}
                for v in vals:
                    if v:
                        tally[v] = tally.get(v, 0) + 1
                sub = "／".join(f"{k} {v}" for k, v in list(tally.items())[:4])
        return len(rows), sub

    bz, bz_sub = count("business-requirements.md", "BZ-", "MoSCoW")
    uc, _ = count("use-cases.md", "UC-")
    nfr, nfr_sub = count("non-functional.md", "NFR-")
    oq_all, _ = count("open-questions.md", "OQ-")
    oq_open, _ = count("open-questions.md", "OQ-", "ステータス", "open")
    rfp, rfp_sub = count("rfp-analysis.md", "RFP-", "判定")
    kpis = [it for it in [
        {"label": "RFP 要求", "value": rfp, "sub": rfp_sub, "_file": "rfp-analysis.md"},
        {"label": "業務要件（BZ）", "value": bz, "sub": bz_sub, "_file": "business-requirements.md"},
        {"label": "ユースケース（UC）", "value": uc, "_file": "use-cases.md"},
        {"label": "非機能要件（NFR）", "value": nfr, "_file": "non-functional.md"},
        {"label": "要確認事項（OQ）", "value": oq_all, "sub": f"うち未決 {oq_open} 件", "_file": "open-questions.md"},
    ] if it.pop("_file") in sources]
    slides = [
        {"type": "section", "title": "要件の全体像", "message": "RFP の要求を分解し、業務要件とシステム要件に整理しました"},
        {"type": "kpi", "title": "要件の規模", "message": "要件の件数と、まだ決まっていない事項の数です",
         "items": kpis},
        {"type": "table", "title": "業務要件一覧", "from": {"file": "business-requirements.md", "id_prefix": "BZ-", "columns": ["ID", "要求", "MoSCoW", "採否"]}},
        {"type": "table", "title": "ユースケース一覧", "from": {"file": "use-cases.md", "id_prefix": "UC-", "first_table_only": True,
                                                       "columns": ["ID", "ユースケース名", "主アクター", "業務領域"]}},
        {"type": "section", "title": "未決事項と今後の進め方"},
        {"type": "table", "title": "要確認事項（未決）", "message": "期限までにご判断いただきたい事項です",
         "from": {"file": "open-questions.md", "id_prefix": "OQ-", "columns": ["ID", "内容", "確認先", "期限"], "filter": {"column": "ステータス", "equals": "open"}}},
        {"type": "closing", "title": "今後の進め方", "bullets": ["要確認事項へのご回答（期限は一覧のとおり）", "要件定義書のご確認・ご承認", "承認後、基本設計に着手"]},
    ]
    return {"title": prof["powerpoint"]["kind"], "subtitle": "", "slides": slides}


def build(prof: dict, root: Path, sources: dict, out_dir: Path) -> tuple[Path, dict]:
    spec_path = root / "docs/04-deliverables" / prof["powerpoint"].get("spec", "summary-deck.yaml")
    if spec_path.exists():
        spec = yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}
        origin = str(spec_path.relative_to(root))
    else:
        spec = default_spec(prof, sources)
        origin = "既定構成（summary-deck.yaml なし）"
    b = DeckBuilder(prof, root)
    path = b.build(spec, sources, out_dir)
    return path, {"slides": b.page, "spec": origin, "warnings": b.warnings}
