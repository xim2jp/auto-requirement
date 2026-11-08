"""docx_builder.py — 要件定義書（Word）を生成する。

構成：表紙 → 承認欄・改訂履歴 → 目次 → 本編（requirements.md）→ 別紙（BZ / UC / NFR / ROLE / 用語 / OQ / RFP 分析）
- 見出しはアウトライン化（Heading 1〜4）し、目次フィールドは開いたときに更新される
- 表はヘッダー行の色・繰り返し・縞・列幅の自動配分。列数が多い表は横向きページに置く
- Mermaid は mmdc があれば画像化し、無ければソース枠で掲載
- Self-Check / Handoff など社内向けの節は除外する
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT, WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

import common
import mdparse as md
from profile import hex_to_rgb, out_name

A4_W, A4_H = Cm(21.0), Cm(29.7)
MARGIN_TB, MARGIN_LR = Cm(2.2), Cm(2.0)


# --------------------------------------------------------------------------- low-level helpers


def nobreak_ids(run) -> None:
    """ID（SH-01・UC-ORDER-03 等）の中のハイフンを Word の改行しないハイフンにして、ID が行をまたいで割れないようにする。"""
    text = run.text
    if "-" not in text or not md.ID_RE.search(text):
        return
    r = run._element
    for t in r.findall(qn("w:t")):
        r.remove(t)

    def add_text(s: str):
        if not s:
            return
        t = OxmlElement("w:t")
        t.set(qn("xml:space"), "preserve")
        t.text = s
        r.append(t)

    pos = 0
    for m in md.ID_RE.finditer(text):
        add_text(text[pos:m.start()])
        for i, piece in enumerate(m.group(0).split("-")):
            if i:
                r.append(OxmlElement("w:noBreakHyphen"))
            add_text(piece)
        pos = m.end()
    add_text(text[pos:])


def _rgb(h: str) -> RGBColor:
    return RGBColor(*hex_to_rgb(h))


def set_run_font(run, latin: str, east: str, size: float | None = None, bold=None, color: str | None = None):
    run.font.name = latin
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(a), latin)
    rfonts.set(qn("w:eastAsia"), east)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if color:
        run.font.color.rgb = _rgb(color)


def set_style_font(style, latin: str, east: str, size: float | None = None, bold=None, color: str | None = None):
    style.font.name = latin
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.insert(0, rfonts)
    for a in list(rfonts.attrib):
        if a.endswith("Theme"):
            del rfonts.attrib[a]
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rfonts.set(qn(a), latin)
    rfonts.set(qn("w:eastAsia"), east)
    if size:
        style.font.size = Pt(size)
    if bold is not None:
        style.font.bold = bold
    if color:
        style.font.color.rgb = _rgb(color)


def shade(cell_or_par, fill: str):
    el = cell_or_par._tc if hasattr(cell_or_par, "_tc") else cell_or_par._p
    pr = el.get_or_add_tcPr() if hasattr(cell_or_par, "_tc") else el.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    pr.append(shd)


def par_border(par, side: str, color: str, size: int = 8, space: int = 4):
    ppr = par._p.get_or_add_pPr()
    bdr = ppr.find(qn("w:pBdr"))
    if bdr is None:
        bdr = OxmlElement("w:pBdr")
        ppr.append(bdr)
    el = OxmlElement(f"w:{side}")
    el.set(qn("w:val"), "single")
    el.set(qn("w:sz"), str(size))
    el.set(qn("w:space"), str(space))
    el.set(qn("w:color"), color)
    bdr.append(el)


def add_field(par, instr: str, placeholder: str = ""):
    """PAGE / NUMPAGES / TOC などのフィールドを挿入する。"""
    r = par.add_run()
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "begin")
    r._r.append(fc)
    r2 = par.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = f" {instr} "
    r2._r.append(it)
    r3 = par.add_run()
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "separate")
    r3._r.append(fc)
    r4 = par.add_run(placeholder)
    r5 = par.add_run()
    fc = OxmlElement("w:fldChar")
    fc.set(qn("w:fldCharType"), "end")
    r5._r.append(fc)
    return [r, r2, r3, r4, r5]


def repeat_header(row):
    trpr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trpr.append(el)


def cant_split(row):
    trpr = row._tr.get_or_add_trPr()
    trpr.append(OxmlElement("w:cantSplit"))


def keep_next(par) -> None:
    """段落を次の段落と同じページに置く（表のセル内の段落なら、その行を次の行と同じページに置く）。"""
    par.paragraph_format.keep_with_next = True


def page_break_before(p_el) -> None:
    """w:p 要素に「段落前で改ページ」を付ける。"""
    ppr = p_el.get_or_add_pPr()
    if ppr.find(qn("w:pageBreakBefore")) is None:
        el = OxmlElement("w:pageBreakBefore")
        # CT_PPr の子要素順（pStyle・keepNext・keepLines の後）を守る
        anchor = None
        for tag in ("w:keepLines", "w:keepNext", "w:pStyle"):
            anchor = ppr.find(qn(tag))
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addnext(el)
        else:
            ppr.insert(0, el)


def cell_margins(table, top=40, bottom=40, left=80, right=80):
    tblpr = table._tbl.tblPr
    mar = OxmlElement("w:tblCellMar")
    for side, v in (("top", top), ("left", left), ("bottom", bottom), ("right", right)):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:w"), str(v))
        el.set(qn("w:type"), "dxa")
        mar.append(el)
    tblpr.append(mar)


def table_borders(table, color: str):
    tblpr = table._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for side in ("top", "left", "bottom", "right", "insideH", "insideV"):
        el = OxmlElement(f"w:{side}")
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:space"), "0")
        el.set(qn("w:color"), color)
        b.append(el)
    tblpr.append(b)


# --------------------------------------------------------------------------- builder

class WordBuilder:
    def __init__(self, prof: dict, root: Path, spec: dict | None = None):
        self.prof, self.root = prof, root
        self.w = spec or prof["word"]  # この文書の仕様（kind・title・main・appendices・issuer・front）
        self.t = prof["theme"]
        self.doc = Document()
        self.namer = None
        self.landscape = False
        self.cache = root / "tmp/office-cache"
        self.mermaid_mode = prof["output"].get("mermaid", "auto")
        self.stats = {"tables": 0, "figures": 0, "mermaid_source": 0, "landscape_sections": 0}
        self._break_mark = None  # 改ページ待ち：この要素の次に置かれる段落／表の前で改ページする
        self._setup_styles()
        self._setup_page(self.doc.sections[0], landscape=False)

    # ---- styles / page
    def _setup_styles(self):
        t, st = self.t, self.doc.styles
        normal = st["Normal"]
        set_style_font(normal, t["font_latin_body"], t["font_body"], 10.5)
        pf = normal.paragraph_format
        pf.space_after = Pt(4)
        pf.line_spacing = 1.2
        sizes = {1: 16, 2: 13, 3: 11.5, 4: 10.5}
        for lvl, size in sizes.items():
            s = st[f"Heading {lvl}"]
            set_style_font(s, t["font_latin_heading"], t["font_heading"], size, True, t["primary"])
            s.font.italic = False
            s.paragraph_format.space_before = Pt(14 if lvl == 1 else 10)
            s.paragraph_format.space_after = Pt(6 if lvl == 1 else 4)
            s.paragraph_format.keep_with_next = True
        for name in ("Title", "Subtitle"):
            set_style_font(st[name], t["font_latin_heading"], t["font_heading"], None, None, t["primary"])
        for name in ("List Bullet", "List Bullet 2", "List Bullet 3", "List Number"):
            if name in [s.name for s in st]:
                set_style_font(st[name], t["font_latin_body"], t["font_body"], 10.5)
        for lvl in (1, 2, 3):
            name = f"TOC {lvl}"
            try:
                s = st[name]
            except KeyError:
                s = st.add_style(name, 1)
            set_style_font(s, t["font_latin_heading"], t["font_heading"], 10.5 if lvl == 1 else 10, lvl == 1)
            s.paragraph_format.left_indent = Cm(0.6 * (lvl - 1))
            s.paragraph_format.space_before = Pt(0)
            s.paragraph_format.space_after = Pt(1 if lvl == 1 else 0)
            s.paragraph_format.line_spacing = Pt(15)  # 和文フォントの既定の行の高さは大きいため固定値にする
            # Word が目次の更新で使うのは組み込みスタイル「toc N」（小文字）。独自スタイルのままだと無視される
            s.element.find(qn("w:name")).set(qn("w:val"), f"toc {lvl}")
            s.element.attrib.pop(qn("w:customStyle"), None)
        # 既定テンプレートのヘッダー・フッターのタブ位置（縦向きの幅）を消す。残ると横向きページで
        # 段落に足したタブ位置より先に効き、右端に置くはずの文字が中央寄りになる
        for name in ("Header", "Footer"):
            try:
                st[name].paragraph_format.tab_stops.clear_all()
            except KeyError:
                pass

    def _setup_page(self, sec, landscape: bool):
        if landscape:
            sec.orientation = WD_ORIENT.LANDSCAPE
            sec.page_width, sec.page_height = A4_H, A4_W
        else:
            sec.orientation = WD_ORIENT.PORTRAIT
            sec.page_width, sec.page_height = A4_W, A4_H
        sec.top_margin = sec.bottom_margin = MARGIN_TB
        sec.left_margin = sec.right_margin = MARGIN_LR
        sec.header_distance = sec.footer_distance = Cm(1.0)

    def _fig_size(self, png) -> dict:
        """図の大きさ。幅は本文幅（最大 16cm）に合わせ、縦長の図は図の名前と同じページに収まる高さで止める。"""
        sec = self.doc.sections[-1]
        width = min(self._content_width(), Cm(16))
        max_h = sec.page_height - sec.top_margin - sec.bottom_margin - Cm(3)  # 図の名前・前後の余白の分
        try:
            from PIL import Image
            with Image.open(png) as im:
                pw, ph = im.size
        except Exception:
            return {"width": width}
        if pw and ph and width * ph / pw > max_h:
            return {"height": int(max_h)}
        return {"width": width}

    def _content_width(self):
        sec = self.doc.sections[-1]
        return sec.page_width - sec.left_margin - sec.right_margin

    def _header_footer(self, sec):
        p = self.prof["project"]
        w = sec.page_width - sec.left_margin - sec.right_margin
        hp = sec.header.paragraphs[0]
        hp.text = ""
        hp.paragraph_format.tab_stops.add_tab_stop(w, WD_TAB_ALIGNMENT.RIGHT)
        r = hp.add_run(p["confidentiality"])
        set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"], 8, True, "C00000")
        r = hp.add_run(f"\t{self.w['title']}｜{p['name']}")
        set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"], 8, False, self.t["muted"])
        par_border(hp, "bottom", self.t["accent"], 4, 1)

        fp = sec.footer.paragraphs[0]
        fp.text = ""
        fp.paragraph_format.tab_stops.add_tab_stop(w // 2, WD_TAB_ALIGNMENT.CENTER)
        fp.paragraph_format.tab_stops.add_tab_stop(w, WD_TAB_ALIGNMENT.RIGHT)
        r = fp.add_run(p.get("doc_number") or "")
        set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"], 8, False, self.t["muted"])
        fp.add_run("\t")
        for run in add_field(fp, "PAGE", "1"):
            set_run_font(run, self.t["font_latin_heading"], self.t["font_heading"], 8.5, False, self.t["muted"])
        r = fp.add_run(" / ")
        set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"], 8.5, False, self.t["muted"])
        for run in add_field(fp, "NUMPAGES", "1"):
            set_run_font(run, self.t["font_latin_heading"], self.t["font_heading"], 8.5, False, self.t["muted"])
        r = fp.add_run(f"\t{p.get('client', '') if self.w.get('issuer') == 'client' else p['vendor']}")
        set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"], 8, False, self.t["muted"])

    # ---- page breaks
    def _page_break(self):
        """改ページを予約する。改ページだけの段落は置かず、次に置かれる段落（見出しなど）に
        「段落前で改ページ」を付ける。改ページ用の段落はページがちょうど埋まったときに次ページへあふれ、
        空白ページを作るため。"""
        self._resolve_break()
        body = self.doc.element.body
        kids = [k for k in body if k.tag != qn("w:sectPr")]
        self._break_mark = kids[-1] if kids else None

    def _resolve_break(self):
        mark, self._break_mark = self._break_mark, None
        if mark is None:
            return
        nxt = mark.getnext()
        if nxt is None or nxt.tag == qn("w:sectPr"):
            return  # 後ろに何も無い：改ページ不要
        if nxt.tag == qn("w:p"):
            page_break_before(nxt)
        elif nxt.tag == qn("w:tbl"):  # 表の 1 行目のセルの段落に付ける（Word・LibreOffice とも表ごと次ページへ送る）
            ps = nxt.findall(".//" + qn("w:p"))
            if ps:
                page_break_before(ps[0])

    def _new_section(self, landscape: bool):
        mark, self._break_mark = self._break_mark, None  # セクション区切り自体が改ページになる
        body = self.doc.element.body
        tail = [k for k in body if k.tag != qn("w:sectPr")]
        if mark is not None and (not tail or tail[-1] is not mark):
            # 改ページ予約の後に本文が続いている：予約は通常の改ページとして解決し、区切りは本文の末尾に置く
            # （予約位置に区切りを持たせると、その後の本文まで次のセクションの向きになる）
            self._break_mark = mark
            self._resolve_break()
            mark = None
        if mark is None:
            # 直前が表の後の間隔用の空段落なら、それにセクション区切りを持たせる（区切り用の段落を足すと
            # 2 段落がページ末からあふれ、空白ページになる）。持たせる段落は行の高さを最小にする
            body = self.doc.element.body
            last = [k for k in body if k.tag != qn("w:sectPr")]
            last = last[-1] if last else None
            if (last is not None and last.tag == qn("w:p") and not "".join(last.itertext()).strip()
                    and last.find(qn("w:pPr") + "/" + qn("w:sectPr")) is None):
                mark = last
                from docx.text.paragraph import Paragraph
                par = Paragraph(last, self.doc._body)
                par.paragraph_format.space_before = par.paragraph_format.space_after = Pt(0)
                par.paragraph_format.line_spacing = Pt(1)
        sec = self.doc.add_section(WD_SECTION.NEW_PAGE)
        if mark is not None and mark.tag == qn("w:p") and mark.find(qn("w:pPr") + "/" + qn("w:sectPr")) is None:
            # セクション区切りだけの空段落を作らず、直前の段落（目次など）に区切りを持たせる（空白ページ防止）
            body = self.doc.element.body
            new_p = [k for k in body if k.tag != qn("w:sectPr")][-1]
            sp = new_p.find(qn("w:pPr") + "/" + qn("w:sectPr"))
            if sp is not None and new_p is not mark:
                mark.get_or_add_pPr().append(sp)
                body.remove(new_p)
        self._setup_page(sec, landscape)
        sec.different_first_page_header_footer = False
        # ヘッダー・フッターは前セクションにリンクしたままだと横向きでタブ位置がずれるため張り直す
        sec.header.is_linked_to_previous = False
        sec.footer.is_linked_to_previous = False
        self._header_footer(sec)
        self.landscape = landscape
        if landscape:
            self.stats["landscape_sections"] += 1

    # ---- inline
    def _runs(self, par, runs: list[md.Run], size: float | None = None, color: str | None = None, bold=None):
        for r in runs:
            text = self.namer(r.text) if self.namer and not r.code else r.text
            parts = text.split("\n")
            for i, part in enumerate(parts):
                if i:
                    par.add_run().add_break()
                if not part:
                    continue
                run = par.add_run(part)
                if r.code:
                    set_run_font(run, self.t["font_code"], self.t["font_code"], (size or 10.5) - 1)
                    rpr = run._element.get_or_add_rPr()
                    shd = OxmlElement("w:shd")
                    shd.set(qn("w:val"), "clear")
                    shd.set(qn("w:fill"), "F2F2F2")
                    rpr.append(shd)
                else:
                    set_run_font(run, self.t["font_latin_body"], self.t["font_body"], size)
                    nobreak_ids(run)
                run.bold = True if (r.bold or bold) else None
                run.italic = r.italic or None
                run.font.strike = r.strike or None
                if color:
                    run.font.color.rgb = _rgb(color)
                if r.link and r.link.startswith("http") and r.link not in part:
                    tail = par.add_run(f"（{r.link}）")
                    set_run_font(tail, self.t["font_latin_body"], self.t["font_body"], (size or 10.5) - 1.5, False, self.t["muted"])

    # ---- blocks
    def heading(self, text: str, level: int):
        if self.prof["output"].get("strip_heading_emoji", True):
            text = md.strip_emoji(text)
        h = self.doc.add_heading("", level=min(level, 4))
        r = h.add_run(self.namer(text) if self.namer else text)
        set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"])
        if level == 1:
            par_border(h, "bottom", self.t["primary"], 12, 4)
        return h

    def para(self, runs, style=None, indent_cm: float = 0):
        p = self.doc.add_paragraph(style=style)
        if indent_cm:
            p.paragraph_format.left_indent = Cm(indent_cm)
        self._runs(p, runs)
        return p

    def list_block(self, lb: md.ListBlock, depth: int = 0):
        for idx, item in enumerate(lb.items):
            first = True
            for b in item:
                if isinstance(b, md.Para) and first:
                    runs = list(b.runs)
                    if runs and runs[0].text.startswith(("[ ] ", "[x] ", "[X] ")):
                        mark = "☐ " if runs[0].text.startswith("[ ]") else "☑ "
                        runs[0] = md.Run(mark + runs[0].text[4:], runs[0].bold, runs[0].italic)
                    p = self.doc.add_paragraph()
                    pf = p.paragraph_format
                    pf.left_indent = Cm(0.75 + 0.65 * depth)
                    pf.first_line_indent = Cm(-0.5)
                    pf.space_after = Pt(2)
                    marker = f"{lb.start + idx}." if lb.ordered else ("・" if depth == 0 else "－")
                    mr = p.add_run(marker + (" " if lb.ordered else ""))
                    set_run_font(mr, self.t["font_latin_body"], self.t["font_body"], None, None, self.t["accent"])
                    self._runs(p, runs)
                    first = False
                elif isinstance(b, md.ListBlock):
                    self.list_block(b, depth + 1)
                else:
                    self.block(b, indent_cm=0.75 + 0.65 * depth)
                    first = False

    def table(self, tb: md.Table, caption: str | None = None):
        header = tb.header
        ncol = len(header)
        if ncol == 0:
            return
        rows = [r + [[]] * (ncol - len(r)) if len(r) < ncol else r[:ncol] for r in tb.rows]
        self.stats["tables"] += 1
        size = 9 if ncol < 7 else (8 if ncol < 10 else 7)
        if caption:
            cp = self.doc.add_paragraph()
            r = cp.add_run(f"▼ {caption}")
            set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"], 9, True, self.t["primary"])
            cp.paragraph_format.keep_with_next = True
        table = self.doc.add_table(rows=1 + len(rows), cols=ncol)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        table.autofit = False
        table_borders(table, "A6A6A6")
        cell_margins(table)
        weights = common.col_weights([md.plain(c) for c in header], [[md.plain(c) for c in r] for r in rows])
        total = sum(weights)
        width = self._content_width()
        widths = [int(width * w / total) for w in weights]
        # 絶対最小幅：ID と見出し語が 1 行に収まる幅（半角 1 文字 ≒ 0.6 × フォントサイズ（太字込み）、左右余白 8pt + 予備）
        htext, rtext = [md.plain(c) for c in header], [[md.plain(c) for c in r] for r in rows]
        floors = [int(Pt(f * size * 0.6 + 11)) if f else 0 for f in common.col_floors(htext, rtext)]
        if sum(floors) >= width:  # 列が多くて全部は守れない：ID 列だけは守る
            floors = [int(Pt(f * size * 0.6 + 11)) if f else 0 for f in common.col_floors(htext, rtext, ids_only=True)]
        if sum(floors) < width:
            short = [i for i in range(ncol) if widths[i] < floors[i]]
            if short:
                need = sum(floors[i] - widths[i] for i in short)
                rest = [i for i in range(ncol) if i not in short]
                pool = sum(widths[i] - floors[i] for i in rest if widths[i] > floors[i])
                for i in short:
                    widths[i] = floors[i]
                for i in rest:
                    spare = widths[i] - floors[i]
                    if spare > 0 and pool > 0:
                        widths[i] -= int(need * spare / pool)
        for ci, w in enumerate(widths):
            for cell in table.columns[ci].cells:
                cell.width = w
        # header
        hrow = table.rows[0]
        repeat_header(hrow)
        cant_split(hrow)
        for ci, c in enumerate(header):
            cell = hrow.cells[ci]
            shade(cell, self.t["primary"])
            p = cell.paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            keep_next(p)  # 見出し行だけがページ末に残らないよう、1 行目のデータ行と同じページに置く
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            self._runs(p, c, size=size, color="FFFFFF", bold=True)
            for run in p.runs:
                set_run_font(run, self.t["font_latin_heading"], self.t["font_heading"], size, True, "FFFFFF")
        # body
        for ri, r in enumerate(rows, start=1):
            row = table.rows[ri]
            cant_split(row)
            for ci, c in enumerate(r):
                cell = row.cells[ci]
                if ri % 2 == 0:
                    shade(cell, "F5F8FC")
                p = cell.paragraphs[0]
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.1
                if ri == 1 and len(rows) >= 3:  # 1 行目のデータ行も 2 行目と同じページに（見出し行＋1 行だけの取り残しを防ぐ）
                    keep_next(p)
                align = tb.aligns[ci] if ci < len(tb.aligns) else None
                if align == "center":
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                elif align == "right":
                    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                self._runs(p, c, size=size, bold=(ci == 0 and bool(md.find_ids(md.plain(c)))) or None)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def code(self, cb: md.Code):
        if cb.lang == "mermaid":
            mode = self.mermaid_mode
            if mode == "off":
                return
            png = common.mermaid_to_png(cb.text, mode, self.cache)
            if png:
                self.stats["figures"] += 1
                self.doc.add_picture(str(png), **self._fig_size(png))
                self.doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
                return
            self.stats["mermaid_source"] += 1
            cap = self.doc.add_paragraph()
            r = cap.add_run("図（Mermaid 記法。図として表示するには mmdc を導入して再生成）")
            set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"], 8, True, self.t["muted"])
            cap.paragraph_format.keep_with_next = True
        for i, line in enumerate(cb.text.split("\n") or [""]):
            p = self.doc.add_paragraph()
            pf = p.paragraph_format
            pf.space_after = Pt(0)
            pf.line_spacing = 1.0
            pf.left_indent = Cm(0.3)
            shade(p, "F2F2F2")
            r = p.add_run(line if line else " ")
            set_run_font(r, self.t["font_code"], self.t["font_code"], 8.5)
        self.doc.add_paragraph().paragraph_format.space_after = Pt(2)

    def quote(self, q: md.Quote, indent_cm: float = 0):
        for b in q.blocks:
            if isinstance(b, md.Para):
                p = self.doc.add_paragraph()
                p.paragraph_format.left_indent = Cm(0.3 + indent_cm)
                p.paragraph_format.space_after = Pt(2)
                shade(p, self.t["light"])
                par_border(p, "left", self.t["accent"], 18, 6)
                self._runs(p, b.runs, size=9.5)
            else:
                self.block(b, indent_cm=indent_cm + 0.3)

    def block(self, b, indent_cm: float = 0, caption: str | None = None):
        if isinstance(b, md.Heading):
            self.heading(b.text, b.level)
        elif isinstance(b, md.Para):
            self.para(b.runs, indent_cm=indent_cm)
        elif isinstance(b, md.ListBlock):
            self.list_block(b)
        elif isinstance(b, md.Table):
            self.table(b, caption)
        elif isinstance(b, md.Code):
            self.code(b)
        elif isinstance(b, md.Quote):
            self.quote(b, indent_cm)

    def blocks(self, blocks: list, level_shift: int):
        """level_shift: Markdown の見出しレベルから引く数（H2→Heading 1 なら 1）。"""
        wide = self.w.get("landscape_table_columns", self.prof["word"].get("landscape_table_columns", 8))
        last_heading = None
        i = 0
        while i < len(blocks):
            b = blocks[i]
            if isinstance(b, md.Heading):
                # この見出しの直下（次の見出しまで）に横長表があれば、見出しごと横向きページへ
                j, has_wide = i + 1, False
                # 本文の無い親見出し（直後が子見出し）は、子の節まで見て判断する
                while j < len(blocks) and isinstance(blocks[j], md.Heading) and blocks[j].level > b.level:
                    j += 1
                while j < len(blocks) and not isinstance(blocks[j], md.Heading):
                    if isinstance(blocks[j], md.Table) and len(blocks[j].header) >= wide:
                        has_wide = True
                    j += 1
                if has_wide != self.landscape:
                    self._new_section(has_wide)
                lvl = max(1, b.level - level_shift)
                self.heading(b.text, lvl)
                last_heading = b.text
            elif isinstance(b, md.Table) and len(b.header) >= wide and not self.landscape:
                self._new_section(True)
                self.table(b, caption=md.strip_emoji(last_heading) if last_heading else None)
            elif isinstance(b, md.Para):
                p = self.para(b.runs)
                nxt = blocks[i + 1] if i + 1 < len(blocks) else None
                # 表・図の導入文（図の名前を含む）と、「：」で終わるリストの導入文は次と同じページに置く
                if isinstance(nxt, (md.Table, md.Code)) or (
                        isinstance(nxt, md.ListBlock) and md.plain(b.runs).rstrip().endswith(("：", ":"))):
                    if not (isinstance(nxt, md.Table) and len(nxt.header) >= wide and not self.landscape):
                        keep_next(p)
            else:
                self.block(b)
            i += 1

    # ---- front matter
    def cover(self):
        p, t = self.prof["project"], self.t
        w = self.w
        by_client = w.get("issuer") == "client"  # RFP：発注者が発行する文書（宛名なし・発行者＝発注者）
        for _ in range(6):
            self.doc.add_paragraph()
        bar = self.doc.add_paragraph()
        par_border(bar, "top", t["primary"], 36, 1)
        cl = self.doc.add_paragraph()
        if by_client:
            r = cl.add_run(p.get("client", ""))
        else:
            r = cl.add_run(p["client"] + "　御中" if p.get("client") and not p["client"].startswith("（") else p.get("client", ""))
        set_run_font(r, t["font_latin_heading"], t["font_heading"], 14, False, t["muted"])
        tp = self.doc.add_paragraph()
        tp.paragraph_format.space_before = Pt(12)
        r = tp.add_run(p["name"])
        set_run_font(r, t["font_latin_heading"], t["font_heading"], 20, True, t["primary"])
        tt = self.doc.add_paragraph()
        r = tt.add_run(w["title"])
        set_run_font(r, t["font_latin_heading"], t["font_heading"], 30, True, t["primary"])
        if w.get("subtitle"):
            st = self.doc.add_paragraph()
            r = st.add_run(w["subtitle"])
            set_run_font(r, t["font_latin_heading"], t["font_heading"], 13, False, t["muted"])
        if getattr(self, "intro_text", ""):  # 付録文書：冒頭説明を表紙に置く（説明だけのページを作らない）
            ip = self.doc.add_paragraph()
            ip.paragraph_format.space_before = Pt(10)
            r = ip.add_run(self.intro_text)
            set_run_font(r, t["font_latin_body"], t["font_body"], 10.5, False, t["muted"])
        bar2 = self.doc.add_paragraph()
        par_border(bar2, "bottom", t["accent"], 8, 1)
        for _ in range(5 if getattr(self, "intro_text", "") else 8):
            self.doc.add_paragraph()
        ver = f"第 {p['version']} 版" + (f"（{p['status']}）" if p.get("status") else "")
        info = [("文書番号", p.get("doc_number") or "—"), ("版数", ver),
                ("発行日", p["date"]), ("作成", p["vendor"]), ("機密区分", p["confidentiality"])]
        if by_client:
            info[3] = ("発行", p.get("client") or "")
            if p.get("contact"):
                info.insert(4, ("問い合わせ窓口", p["contact"]))
        info = [(k, v) for k, v in info if not (k == "文書番号" and v == "—" and by_client)]
        tb = self.doc.add_table(rows=len(info), cols=2)
        tb.alignment = WD_TABLE_ALIGNMENT.RIGHT
        table_borders(tb, "BFBFBF")
        for i, (k, v) in enumerate(info):
            c0, c1 = tb.rows[i].cells
            c0.width, c1.width = Cm(3), Cm(7)
            shade(c0, t["light"])
            r = c0.paragraphs[0].add_run(k)
            set_run_font(r, t["font_latin_heading"], t["font_heading"], 9.5, True, t["primary"])
            r = c1.paragraphs[0].add_run(str(v))
            set_run_font(r, t["font_latin_heading"], t["font_heading"], 9.5)
        self.doc.sections[0].different_first_page_header_footer = True
        self._header_footer(self.doc.sections[0])
        self._page_break()

    def front_heading(self, text: str):
        """目次に載せない前付けの見出し（承認欄・改訂履歴・目次）。"""
        p = self.doc.add_paragraph()
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        r = p.add_run(text)
        set_run_font(r, self.t["font_latin_heading"], self.t["font_heading"], 16, True, self.t["primary"])
        par_border(p, "bottom", self.t["primary"], 12, 4)
        return p

    def approvals_and_revisions(self):
        p, t = self.prof["project"], self.t
        self.front_heading("承認欄")
        aps = p.get("approvals") or []
        if aps:
            tb = self.doc.add_table(rows=3, cols=len(aps))
            tb.alignment = WD_TABLE_ALIGNMENT.RIGHT
            table_borders(tb, "808080")
            for i, a in enumerate(aps):
                c = tb.rows[0].cells[i]
                shade(c, t["primary"])
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = c.paragraphs[0].add_run(a.get("role", ""))
                set_run_font(r, t["font_latin_heading"], t["font_heading"], 9, True, "FFFFFF")
                c = tb.rows[1].cells[i]
                c.width = Cm(3)
                tb.rows[1].height = Cm(2.2)
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = c.paragraphs[0].add_run(a.get("name", ""))
                set_run_font(r, t["font_latin_heading"], t["font_heading"], 9)
                c = tb.rows[2].cells[i]
                c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
                r = c.paragraphs[0].add_run(a.get("date", "") or "　　/　　/　　")
                set_run_font(r, t["font_latin_heading"], t["font_heading"], 8, False, t["muted"])
        self.doc.add_paragraph()
        self.front_heading("改訂履歴")
        revs = p.get("revisions") or []
        tbl = md.Table(
            header=[[md.Run("版数")], [md.Run("改訂日")], [md.Run("改訂内容")], [md.Run("改訂者")]],
            rows=[[[md.Run(str(r.get("version", "")))], [md.Run(str(r.get("date", "")))],
                   [md.Run(str(r.get("description", "")))], [md.Run(str(r.get("author", "") or ""))]] for r in revs],
        )
        self.table(tbl)
        self._page_break()

    def toc(self, depth: str = "1-2"):
        self.front_heading("目次")
        p = self.doc.add_paragraph()
        add_field(p, f'TOC \\o "{depth}" \\h \\z \\u', "（目次は文書を開いたときに更新されます。更新されない場合は右クリック →「フィールド更新」）")
        # 開いたときにフィールド更新を促す
        settings = self.doc.settings.element
        uf = OxmlElement("w:updateFields")
        uf.set(qn("w:val"), "true")
        settings.append(uf)
        self._page_break()

    # ---- assemble
    def build(self, sources: dict[str, list], out_dir: Path, names: dict[str, str] | None = None) -> Path:
        w, o = self.w, self.prof["output"]
        strip = o.get("strip_internal_sections", [])
        bundled = w.get("appendix_mode", "separate") == "bundled"
        apps = [a for a in w.get("appendices", []) if a["source"] in sources] if bundled else []
        mapping = dict(names or {})
        for n, a in enumerate(apps, start=1):
            mapping[a["source"]] = f"別紙{n}「{a['title']}」"
        mapping[w["main"]] = "本書"
        self.namer = common.DocNamer(mapping)
        if w.get("issuer") == "client" and w["main"] in sources:
            self.prof = {**self.prof, "project": client_project(self.prof, sources[w["main"]], w)}

        self.intro_text = self._intro_text(sources[w["main"]]) if w.get("intro_from_preamble") and w["main"] in sources else ""
        self.cover()
        if w.get("front") != "light":
            self.approvals_and_revisions()
        # 見出し 2 が多い文書（決定ログ・ユースケース一覧など）は、目次を見出し 1 までにして 1 ページに収める
        n2 = sum(1 for b in sources.get(w["main"], []) if isinstance(b, md.Heading) and b.level == 3)
        self.toc("1-1" if n2 > 30 else "1-2")

        if w["main"] in sources:
            main = md.drop_sections(common.body_blocks(sources[w["main"]]), strip)
            self.blocks(main, level_shift=1)
        for n, a in enumerate(apps, start=1):
            blocks = md.drop_sections(common.body_blocks(sources[a["source"]]), strip)
            if self.landscape:
                self._new_section(False)
            else:
                self._page_break()
            self.heading(f"別紙{n}　{a['title']}", 1)
            self._preamble_intro(sources[a["source"]])
            self.blocks(blocks, level_shift=0)

        self._resolve_break()
        cp = self.doc.core_properties
        p = self.prof["project"]
        cp.title = f"{w['title']}｜{p['name']}"
        cp.subject = p["name"]
        cp.author = p.get("author") or p["vendor"]
        cp.category = w["title"]
        cp.keywords = "要件定義; " + p["name"]
        cp.comments = f"第 {p['version']} 版 {p['date']}"
        cp.revision = 1

        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / out_name(self.prof, w["kind"], "docx")
        self.doc.save(path)
        return path


    @staticmethod
    def _intro_text(blocks: list) -> str:
        """「この文書について」の 1 文目（作業用の説明は落とす）。"""
        for q in common.preamble_quote(blocks)[:1]:
            if q.blocks and isinstance(q.blocks[0], md.Para):
                text = md.plain(q.blocks[0].runs).replace("この文書について：", "").strip()
                return text.split("。")[0] + "。" if "。" in text else text
        return ""

    def _preamble_intro(self, blocks: list):
        text = self._intro_text(blocks)
        if text:
            self.quote(md.Quote([md.Para([md.Run(text)])]))


def client_project(prof: dict, blocks: list, spec: dict) -> dict:
    """発注者が発行する文書（RFP）の文書情報。版数・発行日は正本の冒頭表（「発行日 / 版」）から取り、
    作成者・改訂履歴は発注者名義にする。受注者側の文書番号・版数・改訂履歴は持ち込まない。
    rfp_word.project に書いた項目があればそれを優先する。"""
    import re
    p = prof["project"]
    client = p.get("client", "")
    head: dict[str, str] = {}
    for b in blocks:  # 冒頭表は前書き（最初の H2 より前）にある
        if isinstance(b, md.Table):
            for row in b.rows:
                if len(row) >= 2:
                    head[md.plain(row[0]).strip()] = md.plain(row[1]).strip()
            break
    vd = head.get("発行日 / 版", "")
    m_date = re.search(r"\d{4}-\d{2}-\d{2}", vd)
    m_ver = re.search(r"第\s*([0-9.]+)\s*版", vd)
    version = m_ver.group(1) if m_ver else p["version"]
    date = m_date.group(0) if m_date else p["date"]
    out = {**p, "version": version, "date": date, "status": "", "doc_number": "", "author": client,
           "contact": head.get("問い合わせ窓口", ""),
           "revisions": [{"version": version, "date": date, "description": "初版発行", "author": client}]}
    out.update(spec.get("project") or {})
    return out


def plan(prof: dict, sources: dict[str, list]) -> list[dict]:
    """生成する Word 文書の一覧（spec の配列）。RFP（あれば）→ 要件定義書 → 別紙（separate のとき）の順。"""
    specs: list[dict] = []
    w = prof["word"]
    rw = prof.get("rfp_word") or {}
    if rw.get("enabled", True) and rw.get("main") in sources:
        specs.append({**w, "appendices": [], "appendix_mode": "bundled", **rw, "_role": "rfp"})
    if w.get("enabled", True):
        specs.append({**w, "_role": "main"})
        if w.get("appendix_mode", "separate") == "separate":
            apps = [a for a in w.get("appendices", []) if a["source"] in sources]
            for n, a in enumerate(apps, start=1):
                specs.append({**w, "kind": f"別紙{n}_{a['title']}", "title": f"{w['title']} 別紙{n}",
                              "subtitle": a["title"], "main": a["source"], "appendices": [],
                              "front": "light", "intro_from_preamble": True, "_role": "appendix"})
    return specs


doc_names = common.doc_names  # 互換のため残す（正本は common.doc_names）


def build(prof: dict, root: Path, sources: dict[str, list], out_dir: Path) -> tuple[list[Path], dict]:
    names = doc_names(prof, sources)
    paths: list[Path] = []
    stats = {"documents": 0, "tables": 0, "figures": 0, "mermaid_source": 0, "landscape_sections": 0}
    for spec in plan(prof, sources):
        b = WordBuilder(prof, root, spec)
        paths.append(b.build(sources, out_dir, names))
        stats["documents"] += 1
        for k, v in b.stats.items():
            stats[k] = stats.get(k, 0) + v
    return paths, stats
