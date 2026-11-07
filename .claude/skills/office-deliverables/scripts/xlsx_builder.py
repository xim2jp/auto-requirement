"""xlsx_builder.py — 要件一覧（Excel 管理台帳）を生成する。

シート：表紙 → 目次 → 集計 → 各 ID 台帳（RFP / BZ / UC / NFR / ROLE / IF / SH / 用語 / OQ / D）→ トレーサビリティ
- ID 台帳は Markdown 内の表から「1 列目が ID 接頭辞で始まる行」を文書全体から集め、見出し名で列を揃える
- ヘッダー固定・オートフィルタ・列幅自動・折返し・印刷設定（A4 横・幅 1 ページ・見出し行の繰返し）
- 優先度・採否・ステータス列には入力規則と条件付き書式
- 集計シートは COUNTIF 数式で台帳と連動する
"""
from __future__ import annotations

import re
from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter, quote_sheetname
from openpyxl.worksheet.datavalidation import DataValidation

import common
import mdparse as md
from profile import out_name

THIN = Side(style="thin", color="A6A6A6")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)

VALIDATIONS = [
    # (列見出しに含まれる語, 候補)
    (("MoSCoW", "優先度"), ["Must", "Should", "Could", "Won't"]),
    (("採否",), ["採用", "先送り", "棄却", "保留"]),
    (("ステータス", "状態"), ["open", "answered", "closed", "deferred"]),
    (("判定",), ["一致", "明確", "補完", "曖昧", "矛盾", "欠落", "対象外"]),
]

MOSCOW_FILL = {"Must": "F8CBAD", "Should": "FFE699", "Could": "C6E0B4", "Won't": "D9D9D9"}


class ExcelBuilder:
    def __init__(self, prof: dict, root: Path):
        self.prof, self.root = prof, root
        t = prof["theme"]
        self.t = t
        self.font = t["font_ui"]
        self.wb = Workbook()
        self.f_head = Font(name=self.font, bold=True, color="FFFFFF", size=10)
        self.fill_head = PatternFill("solid", fgColor=t["primary"])
        self.fill_zebra = PatternFill("solid", fgColor="F5F8FC")
        self.fill_light = PatternFill("solid", fgColor=t["light"])
        self.f_body = Font(name=self.font, size=10)
        self.f_id = Font(name=self.font, size=10, bold=True, color=t["primary"])
        self.ledgers: list[dict] = []  # {name, ws, header, rows}
        self.stats: dict = {}

    # ---------------------------------------------------------------- collect
    @staticmethod
    def collect(blocks: list, spec: dict) -> tuple[list[str], list[list[str]]]:
        prefix = spec.get("id_prefix")
        heading = spec.get("heading")
        header: list[str] = []
        rows: list[list[str]] = []
        seen: set[str] = set()
        add_section_col = False
        found_tables = 0
        for path, tb in md.iter_tables_with_context(blocks):
            h = [x.strip() for x in tb.header_text()]
            body = tb.rows_text()
            if prefix:
                hits = [r for r in body if r and r[0].strip().startswith(prefix)]
                if not hits:
                    continue
            elif heading:
                if not any(heading in p for p in path):
                    continue
                hits = body
            else:
                continue
            found_tables += 1
            if spec.get("first_table_only") and found_tables > 1:
                break
            sec_name = md.strip_emoji(path[-1]) if path else ""
            if found_tables > 1:
                add_section_col = True
            cols = [_match_col(col, header) for col in h]
            for col in cols:
                if col not in header:
                    header.append(col)
            for r in hits:
                key = r[0].strip()
                if prefix and key in seen:
                    continue
                seen.add(key)
                rec = {cols[i]: (r[i] if i < len(r) else "") for i in range(len(h))}
                rec["__section"] = sec_name
                rows.append(rec)
        if not header:
            return [], []
        if add_section_col:
            header = header[:1] + ["区分"] + header[1:]
            for rec in rows:
                rec["区分"] = rec["__section"]
        return header, [[rec.get(c, "") for c in header] for rec in rows]

    @staticmethod
    def groups(blocks: list, spec: dict) -> list[tuple[str, list[str], list[list[str]]]]:
        """列構成が大きく異なる表（例：目的系 BZ と手段系 BZ）を別グループに分ける。
        列名の重なりが 6 割以上の表は同じグループにまとめる。"""
        prefix = spec.get("id_prefix")
        if not prefix or spec.get("first_table_only"):
            h, r = ExcelBuilder.collect(blocks, spec)
            return [("", h, r)] if r else []
        tables = []
        for path, tb in md.iter_tables_with_context(blocks):
            if any(r and r[0].strip().startswith(prefix) for r in tb.rows_text()):
                tables.append((md.strip_emoji(path[-1]) if path else "", tb))
        grouped: list[list] = []  # [label, header_set, [tables]]
        for label, tb in tables:
            hs = set(_norm(x) for x in tb.header_text())
            for g in grouped:
                if len(hs & g[1]) / max(len(hs | g[1]), 1) >= 0.6:
                    g[1] |= hs
                    g[2].append(tb)
                    break
            else:
                grouped.append([label, hs, [tb]])
        out: list[list] = []  # [label, header, rows]
        where: dict[str, tuple[int, int]] = {}  # ID → (out の添字, 行の添字)
        for label, _, tbs in grouped:
            h, r = ExcelBuilder.collect(tbs, spec)
            if not r:
                continue
            ids = [str(x[0]).strip() for x in r]
            if out and all(i in where for i in ids):
                # 既出 ID を参照するだけの表（対象外の理由・論点一覧など）は、主台帳に列として足す
                for row in r:
                    gi, ri = where[str(row[0]).strip()]
                    gh, grows = out[gi][1], out[gi][2]
                    for ci, col in enumerate(h[1:], start=1):
                        key = _match_col(col, gh)
                        if key not in gh:
                            gh.append(key)
                            for g in grows:
                                g.append("")
                        idx = gh.index(key)
                        if not str(grows[ri][idx]).strip():
                            grows[ri][idx] = row[ci] if ci < len(row) else ""
                continue
            keep = [x for x in r if str(x[0]).strip() not in where]
            out.append([label, h, keep])
            for ri, x in enumerate(keep):
                where[str(x[0]).strip()] = (len(out) - 1, ri)
        return [tuple(x) for x in out]

    # ---------------------------------------------------------------- sheet writers
    def _title_row(self, ws, title: str, note: str, ncol: int):
        ws["A1"] = title
        ws["A1"].font = Font(name=self.font, size=14, bold=True, color=self.t["primary"])
        ws["A2"] = note
        ws["A2"].font = Font(name=self.font, size=9, color=self.t["muted"])
        ws.row_dimensions[1].height = 24

    def ledger(self, name: str, header: list[str], rows: list[list[str]], source: str):
        title, n = name[:31], 2
        while title in self.wb.sheetnames:
            title = f"{name[:28]}({n})"
            n += 1
        ws = self.wb.create_sheet(title)
        ncol = len(header)
        self._title_row(ws, name, f"出典：{source_title(self.prof, source)}／ {len(rows)} 件", ncol)
        HR = 4
        for ci, h in enumerate(header, start=1):
            c = ws.cell(row=HR, column=ci, value=h)
            c.font, c.fill, c.border = self.f_head, self.fill_head, BORDER
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[HR].height = 30
        for ri, r in enumerate(rows, start=HR + 1):
            for ci, v in enumerate(r, start=1):
                val = _cell_value(v)
                c = ws.cell(row=ri, column=ci, value=val)
                c.border = BORDER
                c.alignment = Alignment(vertical="top", wrap_text=True)
                c.font = self.f_id if ci == 1 else self.f_body
                if (ri - HR) % 2 == 0:
                    c.fill = self.fill_zebra
        last = HR + max(len(rows), 1)
        # 列幅
        weights = common.col_weights(header, rows, min_w=6, max_w=50)
        for ci, w in enumerate(weights, start=1):
            ws.column_dimensions[get_column_letter(ci)].width = min(55, max(8, w * 1.1 + 2))
        ws.freeze_panes = ws.cell(row=HR + 1, column=2)
        ref = f"A{HR}:{get_column_letter(ncol)}{last}"
        ws.auto_filter.ref = ref
        # 入力規則・条件付き書式
        for ci, h in enumerate(header, start=1):
            col = get_column_letter(ci)
            rng = f"{col}{HR + 1}:{col}{max(last, HR + 200)}"
            for keys, options in VALIDATIONS:
                if any(k in h for k in keys):
                    vals = {str(r[ci - 1]).strip() for r in rows if ci - 1 < len(r) and str(r[ci - 1]).strip()}
                    if vals and not vals.issubset(set(options)):
                        break  # 既存値が候補外（自由記述）なら規則を付けない
                    dv = DataValidation(type="list", formula1='"' + ",".join(options) + '"', allow_blank=True)
                    dv.error, dv.errorTitle = "候補から選択してください", "入力規則"
                    ws.add_data_validation(dv)
                    dv.add(rng)
                    break
            if any(k in h for k in ("MoSCoW", "優先度")):
                for val, color in MOSCOW_FILL.items():
                    ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{val}"'], fill=PatternFill("solid", fgColor=color)))
            if "採否" in h:
                ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"棄却"'], font=Font(color="808080", strike=True)))
            if any(k in h for k in ("ステータス", "状態")):
                ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=['"open"'], fill=PatternFill("solid", fgColor="FCE4D6"), font=Font(bold=True, color="C00000")))
            if h.strip() == "判定":
                for val, color in (("矛盾", "F8CBAD"), ("欠落", "FFE699"), ("曖昧", "FFF2CC")):
                    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'ISNUMBER(SEARCH("{val}",{col}{HR + 1}))'], fill=PatternFill("solid", fgColor=color)))
        self._print(ws, HR)
        self.ledgers.append({"name": ws.title, "ws": ws, "header": header, "rows": rows, "hr": HR, "source": source})
        return ws

    def _print(self, ws, header_row: int):
        ws.page_setup.orientation = "landscape"
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.print_title_rows = f"{header_row}:{header_row}"
        ws.page_margins.left = ws.page_margins.right = 0.4
        ws.page_margins.top = ws.page_margins.bottom = 0.6
        p = self.prof["project"]
        ws.oddHeader.left.text = p["confidentiality"]
        ws.oddHeader.right.text = f"{p['name']}　{ws.title}"
        ws.oddFooter.center.text = "&P / &N"
        ws.oddFooter.right.text = f"第 {p['version']} 版　{p['date']}"
        ws.sheet_view.zoomScale = 90

    @staticmethod
    def _fit_page(ws, orientation):
        ws.page_setup.orientation = orientation
        ws.page_setup.paperSize = ws.PAPERSIZE_A4
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr.fitToPage = True

    def cover(self):
        ws = self.wb.active
        ws.title = "表紙"
        p, x = self.prof["project"], self.prof["excel"]
        ws.sheet_view.showGridLines = False
        ws.column_dimensions["A"].width = 3
        ws.column_dimensions["B"].width = 18
        ws.column_dimensions["C"].width = 60
        ws["B3"] = p["name"]
        ws["B3"].font = Font(name=self.font, size=16, bold=True, color=self.t["muted"])
        ws["B4"] = x["title"]
        ws["B4"].font = Font(name=self.font, size=26, bold=True, color=self.t["primary"])
        ws.row_dimensions[4].height = 40
        info = [("発注者", p["client"]), ("作成", p["vendor"]), ("文書番号", p.get("doc_number") or "—"),
                ("版数", f"第 {p['version']} 版（{p.get('status') or ''}）"), ("発行日", p["date"]), ("機密区分", p["confidentiality"]),
                ("関連文書", f"{self.prof['word']['title']}（Word）／{self.prof['powerpoint']['kind']}（PowerPoint）")]
        for i, (k, v) in enumerate(info, start=7):
            a, b = ws.cell(row=i, column=2, value=k), ws.cell(row=i, column=3, value=v)
            a.font = Font(name=self.font, bold=True, color=self.t["primary"])
            a.fill = self.fill_light
            b.font = self.f_body
            a.border = b.border = BORDER
        r0 = 7 + len(info) + 2
        ws.cell(row=r0, column=2, value="改訂履歴").font = Font(name=self.font, size=12, bold=True, color=self.t["primary"])
        heads = ["版数", "改訂日", "改訂内容", "改訂者"]
        ws.column_dimensions["D"].width = 40
        ws.column_dimensions["E"].width = 16
        for ci, h in enumerate(heads, start=2):
            c = ws.cell(row=r0 + 1, column=ci, value=h)
            c.font, c.fill, c.border = self.f_head, self.fill_head, BORDER
        for ri, rv in enumerate(p.get("revisions") or [], start=r0 + 2):
            for ci, k in enumerate(("version", "date", "description", "author"), start=2):
                c = ws.cell(row=ri, column=ci, value=str(rv.get(k, "") or ""))
                c.font, c.border = self.f_body, BORDER
        self._fit_page(ws, "portrait")

    def index_sheet(self):
        ws = self.wb.create_sheet("目次", 1)
        ws.sheet_view.showGridLines = False
        self._title_row(ws, "目次", "シート名をクリックすると移動します", 4)
        heads = ["No.", "シート", "件数", "出典", "内容"]
        widths = [6, 26, 8, 30, 50]
        for ci, (h, w) in enumerate(zip(heads, widths), start=1):
            c = ws.cell(row=4, column=ci, value=h)
            c.font, c.fill, c.border = self.f_head, self.fill_head, BORDER
            ws.column_dimensions[get_column_letter(ci)].width = w
        entries = [("集計", "", "", "件数・優先度・採否・未決の集計（数式で各台帳と連動）")] if "集計" in self.wb.sheetnames else []
        entries += [(l["name"], len(l["rows"]), source_title(self.prof, l["source"]), "") for l in self.ledgers]
        if "トレーサビリティ" in self.wb.sheetnames:
            entries.append(("トレーサビリティ", "", "生成", "RFP → BZ → UC の対応と未対応の検出"))
        for i, (name, n, src, desc) in enumerate(entries, start=1):
            r = 4 + i
            vals = [i, name, n, src, desc]
            for ci, v in enumerate(vals, start=1):
                c = ws.cell(row=r, column=ci, value=v)
                c.border, c.font = BORDER, self.f_body
            link = ws.cell(row=r, column=2)
            link.hyperlink = f"#{quote_sheetname(name)}!A1"
            link.font = Font(name=self.font, color="0563C1", underline="single")
        self._fit_page(ws, "portrait")

    def summary_sheet(self):
        ws = self.wb.create_sheet("集計", 1)
        ws.sheet_view.showGridLines = False
        self._title_row(ws, "集計", "各台帳シートの COUNTIF 数式で自動集計（台帳を編集すると更新されます）", 4)
        ws.column_dimensions["A"].width = 26
        for col in "BCDEFG":
            ws.column_dimensions[col].width = 12
        r = 4
        heads = ["台帳", "件数"]
        for ci, h in enumerate(heads, start=1):
            c = ws.cell(row=r, column=ci, value=h)
            c.font, c.fill, c.border = self.f_head, self.fill_head, BORDER
        for l in self.ledgers:
            r += 1
            hr, ref = l["hr"], quote_sheetname(l["name"])
            ws.cell(row=r, column=1, value=l["name"]).border = BORDER
            c = ws.cell(row=r, column=2, value=f"=COUNTA({ref}!A{hr + 1}:A{hr + 2000})")
            c.border = BORDER
        r += 2
        # 列値の分布（MoSCoW・採否・ステータス・判定）
        for l in self.ledgers:
            for ci, h in enumerate(l["header"], start=1):
                for keys, options in VALIDATIONS:
                    if not any(k in h for k in keys):
                        continue
                    present = {str(x[ci - 1]).strip() for x in l["rows"] if ci - 1 < len(x)}
                    if not present & set(options):
                        break
                    col = get_column_letter(ci)
                    ref = quote_sheetname(l["name"])
                    ws.cell(row=r, column=1, value=f"{l['name']}：{h}").font = Font(name=self.font, bold=True, color=self.t["primary"])
                    for oi, opt in enumerate(options, start=2):
                        hc = ws.cell(row=r + 1, column=oi, value=opt)
                        hc.font, hc.fill, hc.border = self.f_head, self.fill_head, BORDER
                        rng = f"{ref}!{col}{l['hr'] + 1}:{col}{l['hr'] + 2000}"
                        vc = ws.cell(row=r + 2, column=oi, value=f'=COUNTIF({rng},"{opt}*")')
                        vc.border = BORDER
                        vc.alignment = Alignment(horizontal="center")
                    ws.cell(row=r + 1, column=1, value="値").border = BORDER
                    ws.cell(row=r + 2, column=1, value="件数").border = BORDER
                    r += 4
                    break
        self._fit_page(ws, "portrait")

    def traceability(self):
        """RFP → BZ → UC の対応表。各台帳の行テキストに現れる ID から機械的に作る。"""

        def ledger_with(prefix):
            ls = [l for l in self.ledgers if l["rows"] and str(l["rows"][0][0]).startswith(prefix)]
            if not ls:
                return None
            return {"rows": [r for l in ls for r in l["rows"]]}

        rfp, bz, uc = ledger_with("RFP-"), ledger_with("BZ-"), ledger_with("UC-")
        if not (bz and uc):
            return
        ws = self.wb.create_sheet("トレーサビリティ")
        self._title_row(ws, "トレーサビリティ", "台帳の記載から ID の参照関係を機械抽出。● ＝ 参照あり／空欄行 ＝ 対応漏れの候補", 4)
        bz_ids = [str(r[0]).strip() for r in bz["rows"]]
        uc_rows = [(str(r[0]).strip(), " ".join(map(str, r))) for r in uc["rows"]]
        # BZ × UC
        HR = 4
        ws.cell(row=HR, column=1, value="BZ ＼ UC")
        ws.cell(row=HR, column=2, value="BZ 名称・内容")
        for ci, (uid, _) in enumerate(uc_rows, start=3):
            c = ws.cell(row=HR, column=ci, value=uid)
            c.alignment = Alignment(text_rotation=90, horizontal="center")
            ws.column_dimensions[get_column_letter(ci)].width = 4.5
        cnt_col = 3 + len(uc_rows)
        ws.cell(row=HR, column=cnt_col, value="UC 数")
        for ci in range(1, cnt_col + 1):
            c = ws.cell(row=HR, column=ci)
            c.font, c.fill, c.border = self.f_head, self.fill_head, BORDER
        ws.row_dimensions[HR].height = 110
        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 40
        ws.column_dimensions[get_column_letter(cnt_col)].width = 8
        for ri, brow in enumerate(bz["rows"], start=HR + 1):
            bid = str(brow[0]).strip()
            ws.cell(row=ri, column=1, value=bid).font = self.f_id
            ws.cell(row=ri, column=2, value=_short(" ".join(map(str, brow[1:3])))).font = self.f_body
            for ci, (uid, text) in enumerate(uc_rows, start=3):
                c = ws.cell(row=ri, column=ci, value="●" if re.search(rf"\b{re.escape(bid)}\b", text) else None)
                c.alignment = Alignment(horizontal="center")
                c.border = BORDER
                c.font = Font(name=self.font, color=self.t["accent"])
            rng = f"C{ri}:{get_column_letter(cnt_col - 1)}{ri}"
            ws.cell(row=ri, column=cnt_col, value=f'=COUNTIF({rng},"●")').border = BORDER
            ws.cell(row=ri, column=1).border = ws.cell(row=ri, column=2).border = BORDER
        last = HR + len(bz["rows"])
        cc = get_column_letter(cnt_col)
        ws.conditional_formatting.add(f"A{HR + 1}:{cc}{last}", FormulaRule(formula=[f"${cc}{HR + 1}=0"], fill=PatternFill("solid", fgColor="FCE4D6")))
        ws.freeze_panes = ws.cell(row=HR + 1, column=3)
        r = last + 3
        # RFP → 参照 ID
        if rfp:
            ws.cell(row=r, column=1, value="RFP 要求 → 対応する要件 ID").font = Font(name=self.font, size=12, bold=True, color=self.t["primary"])
            r += 1
            for ci, h in enumerate(["RFP", "要求（要約）", "BZ", "UC", "NFR", "OQ"], start=1):
                c = ws.cell(row=r, column=ci, value=h)
                c.font, c.fill, c.border = self.f_head, self.fill_head, BORDER
            start = r + 1
            for row in rfp["rows"]:
                r += 1
                text = " ".join(map(str, row[1:]))
                ids = md.find_ids(text)
                vals = [str(row[0]).strip(), _short(str(row[1]) if len(row) > 1 else ""),
                        ", ".join(sorted({i for i in ids if i.startswith("BZ-")})),
                        ", ".join(sorted({i for i in ids if i.startswith("UC-")})),
                        ", ".join(sorted({i for i in ids if i.startswith("NFR-")})),
                        ", ".join(sorted({i for i in ids if i.startswith("OQ-")}))]
                for ci, v in enumerate(vals, start=1):
                    c = ws.cell(row=r, column=ci, value=v)
                    c.border, c.font = BORDER, (self.f_id if ci == 1 else self.f_body)
                    c.alignment = Alignment(wrap_text=True, vertical="top")
            ws.conditional_formatting.add(f"A{start}:F{r}", FormulaRule(formula=[f'AND($C{start}="",$D{start}="",$E{start}="",$F{start}="")'], fill=PatternFill("solid", fgColor="FCE4D6")))
        self._print(ws, HR)
        uncovered = [b for b in bz_ids if not any(re.search(rf"\b{re.escape(b)}\b", t) for _, t in uc_rows)]
        self.stats["bz_without_uc"] = uncovered

    # ---------------------------------------------------------------- assemble
    def build(self, sources: dict[str, list], out_dir: Path) -> Path:
        x = self.prof["excel"]
        self.prof["_present"] = set(sources)
        self.cover()
        for spec in x.get("sheets", []):
            blocks = sources.get(spec["source"])
            if not blocks:
                continue
            gs = self.groups(blocks, spec)
            for label, header, rows in gs:
                name = spec["name"] if len(gs) == 1 else sheet_label(spec["name"], label)
                self.ledger(name, header, rows, spec["source"])
                self.stats[name] = len(rows)
        if x.get("traceability", True):
            self.traceability()
        if x.get("summary", True):
            self.summary_sheet()
        self.index_sheet()
        p = self.prof["project"]
        self.wb.properties.title = f"{x['title']}｜{p['name']}"
        self.wb.properties.creator = p.get("author") or p["vendor"]
        self.wb.properties.subject = p["name"]
        self.wb.properties.keywords = "要件定義; 要件一覧"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / out_name(self.prof, x["kind"], "xlsx")
        self.wb.save(path)
        return path


def source_title(prof: dict, source: str) -> str:
    """台帳の出典を、納品文書での呼び名（本書／別紙N「…」）で返す。"""
    w = prof["word"]
    if source == w["main"]:
        return f"{w['title']} 本編"
    present = prof.get("_present")
    apps = [a for a in w.get("appendices", []) if present is None or a["source"] in present]
    for n, a in enumerate(apps, start=1):
        if a["source"] == source:
            return f"{w['title']} 別紙{n}「{a['title']}」"
    return source


def _norm(h: str) -> str:
    return re.sub(r"[（(][^）)]*[）)]", "", h).strip()


def _match_col(h: str, existing: list[str]) -> str:
    """「要件（値・レベル）」と「要件」、「Tier A 既定値との差分理由」と「差分理由」を同じ列とみなす。"""
    n = _norm(h)
    for k in existing:
        nk = _norm(k)
        if n == nk or (len(nk) >= 3 and n.endswith(nk)) or (len(n) >= 3 and nk.endswith(n)):
            return k
    return h.strip()


def sheet_label(base: str, section: str) -> str:
    """「3.1 目的系要求（業務目的・目標）」→「業務要件(BZ)_目的系要求」（31 文字以内）。"""
    sec = re.sub(r"^[0-9.\s§]+", "", section)
    sec = re.split(r"[（(]", sec)[0].strip()
    for ch in '[]:*?/\\':
        sec = sec.replace(ch, "")
    return f"{base}_{sec}"[:31] if sec else base[:31]


def _cell_value(v: str):
    s = str(v).strip()
    if re.fullmatch(r"-?(0|[1-9]\d{0,11})", s):
        return int(s)
    if re.fullmatch(r"-?\d+\.\d+", s):
        return float(s)
    return s


def _short(s: str, n: int = 80) -> str:
    s = s.replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def build(prof: dict, root: Path, sources: dict[str, list], out_dir: Path) -> tuple[Path, dict]:
    b = ExcelBuilder(prof, root)
    path = b.build(sources, out_dir)
    return path, b.stats
