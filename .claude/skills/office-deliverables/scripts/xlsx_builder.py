"""xlsx_builder.py — 要件一覧（Excel 管理台帳）を生成する。

シート：表紙 → 目次 → 集計 → 各 ID 台帳（RFP / BZ / UC / NFR / ROLE / IF / SH / 用語 / OQ / D）→ トレーサビリティ（BZ × UC）→ トレーサビリティ(RFP)
- ID 台帳は Markdown 内の表から「1 列目が ID 接頭辞で始まる行」を文書全体から集め、見出し名で列を揃える
- ヘッダー固定・オートフィルタ・列幅自動・折返し・印刷設定（A4 横・幅 1 ページ・見出し行の繰返し）
- 優先度・採否・ステータス列には入力規則と条件付き書式
- トレーサビリティは BZ × UC（UC 不要の理由付き）と RFP 要求 → 対応先の 2 シート
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
        self.namer = lambda s: s  # build() でファイル名 → 納品文書名の置換に差し替える

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
                val = _cell_value(self.namer(str(v)))
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
            # 見出しの英字語（MoSCoW など）は太字で途中から折り返さない幅を確保する
            word = max((len(t) for t in re.split(r"[^A-Za-z']+", header[ci - 1]) if t), default=0)
            ws.column_dimensions[get_column_letter(ci)].width = min(55, max(8, w * 1.1 + 2, word * 1.3 + 3))
        _fit_rows(ws, HR + 1, last, ncol)  # 折り返す行の高さ（PDF 化・印刷で文字が切れないように）
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
            entries.append(("トレーサビリティ", "", "生成", "BZ → UC の対応と、UC の無い BZ の理由・対応漏れ候補"))
        if "トレーサビリティ(RFP)" in self.wb.sheetnames:
            entries.append(("トレーサビリティ(RFP)", "", "生成", "RFP 要求 → 対応する要件（BZ・UC・NFR・その他）と対応漏れ候補"))
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
        """BZ × UC の対応表（「トレーサビリティ」）と RFP 要求 → 対応先の表（「トレーサビリティ(RFP)」）。
        各台帳の行テキストに現れる ID から機械的に作る。"""

        def ledger_with(prefix):
            ls = [l for l in self.ledgers if l["rows"] and str(l["rows"][0][0]).startswith(prefix)]
            if not ls:
                return None
            # items：(行, その行の台帳の見出し, 台帳名)。台帳ごとに列構成が違う（目的系 BZ と手段系 BZ など）ため保持する
            return {"rows": [r for l in ls for r in l["rows"]],
                    "items": [(r, l["header"], l["name"]) for l in ls for r in l["rows"]]}

        rfp, bz, uc = ledger_with("RFP-"), ledger_with("BZ-"), ledger_with("UC-")
        if bz and uc:
            self._trace_bz_uc(bz, uc)
        if rfp:
            self._trace_rfp(rfp)

    def _trace_bz_uc(self, bz: dict, uc: dict):
        ws = self.wb.create_sheet("トレーサビリティ")
        self._title_row(ws, "トレーサビリティ（BZ × UC）",
                        "台帳の記載から ID の参照関係を機械抽出。● ＝ 参照あり／灰色の行 ＝ UC が不要な BZ（理由を表示）／"
                        "色付きの行 ＝ UC の無い採用 BZ（対応漏れの候補）", 4)
        uc_rows = [(str(r[0]).strip(), " ".join(map(str, r))) for r in uc["rows"]]
        HR = 4
        fixed = ["BZ ＼ UC", "BZ 名称・内容", "採否", "UC 対象外の理由"]
        UC0 = len(fixed) + 1  # UC 列の開始
        for ci, h in enumerate(fixed, start=1):
            ws.cell(row=HR, column=ci, value=h).alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        for ci, (uid, _) in enumerate(uc_rows, start=UC0):
            c = ws.cell(row=HR, column=ci, value=uid)
            c.alignment = Alignment(text_rotation=90, horizontal="center")
            ws.column_dimensions[get_column_letter(ci)].width = 4.5
        cnt_col = UC0 + len(uc_rows)
        ws.cell(row=HR, column=cnt_col, value="UC 数")
        for ci in range(1, cnt_col + 1):
            c = ws.cell(row=HR, column=ci)
            c.font, c.fill, c.border = self.f_head, self.fill_head, BORDER
        ws.row_dimensions[HR].height = 110
        for col, w in (("A", 12), ("B", 40), ("C", 18), ("D", 34)):
            ws.column_dimensions[col].width = w
        ws.column_dimensions[get_column_letter(cnt_col)].width = 8
        gaps, excused = [], {}
        f_muted = Font(name=self.font, size=9, color="595959")
        for ri, (brow, header, lname) in enumerate(bz["items"], start=HR + 1):
            bid = str(brow[0]).strip()
            adopt = _col_value(brow, header, ("採否",))
            covered = False
            for ci, (uid, text) in enumerate(uc_rows, start=UC0):
                hit = bool(re.search(rf"\b{re.escape(bid)}\b", text))
                covered = covered or hit
                c = ws.cell(row=ri, column=ci, value="●" if hit else None)
                c.alignment = Alignment(horizontal="center")
                c.border = BORDER
                c.font = Font(name=self.font, color=self.t["accent"])
            reason = "" if covered else _uc_exempt_reason(brow, header, lname, adopt)
            if not covered:
                (excused.__setitem__(bid, reason) if reason else gaps.append(bid))
            vals = [bid, _short("／".join(str(x).strip() for x in brow[1:3] if str(x).strip())), _short(adopt, 40), reason]
            for ci, v in enumerate(vals, start=1):
                c = ws.cell(row=ri, column=ci, value=self.namer(v) if v else None)
                c.border = BORDER
                c.font = self.f_id if ci == 1 else (f_muted if ci >= 3 else self.f_body)
                c.alignment = Alignment(vertical="top", wrap_text=True)
            rng = f"{get_column_letter(UC0)}{ri}:{get_column_letter(cnt_col - 1)}{ri}"
            ws.cell(row=ri, column=cnt_col, value=f'=COUNTIF({rng},"●")').border = BORDER
        last = HR + len(bz["items"])
        cc = get_column_letter(cnt_col)
        area = f"A{HR + 1}:{cc}{last}"
        # UC 不要の理由がある行は灰色、理由の無い UC 0 件の行は対応漏れの候補として色付け
        ws.conditional_formatting.add(area, FormulaRule(formula=[f'$D{HR + 1}<>""'], fill=PatternFill("solid", fgColor="EDEDED"), font=Font(color="808080")))
        ws.conditional_formatting.add(area, FormulaRule(formula=[f'AND(${cc}{HR + 1}=0,$D{HR + 1}="")'], fill=PatternFill("solid", fgColor="FCE4D6")))
        _fit_rows(ws, HR + 1, last, UC0 - 1)
        ws.freeze_panes = ws.cell(row=HR + 1, column=UC0)
        ws.auto_filter.ref = f"A{HR}:{cc}{last}"
        self._print(ws, HR)
        self.stats["bz_without_uc"] = gaps + list(excused)
        self.stats["bz_without_uc_gap"] = gaps
        self.stats["bz_without_uc_excused"] = excused

    def _trace_rfp(self, rfp: dict):
        """RFP 要求 → 対応する要件 ID。BZ・UC・NFR 以外の対応先（ROLE・制約・本書の節など）も「その他の対応先」に出す。"""
        ws = self.wb.create_sheet("トレーサビリティ(RFP)")
        self._title_row(ws, "トレーサビリティ（RFP 要求 → 対応する要件）",
                        "RFP 要求分析表の記載から対応先を機械抽出。色付きの行 ＝ 対応先が無く、扱いも対象外・先送りでない要求（対応漏れの候補）", 4)
        HR = 4
        header = rfp["items"][0][1] if rfp["items"] else []
        has_handling = any("扱い" in h for h in header)
        heads = ["RFP", "要求（要約）"] + (["要件定義での扱い"] if has_handling else []) + ["BZ", "UC", "NFR", "その他の対応先", "OQ"]
        widths = {"RFP": 10, "要求（要約）": 50, "要件定義での扱い": 16, "BZ": 18, "UC": 22, "NFR": 18, "その他の対応先": 26, "OQ": 12}
        for ci, h in enumerate(heads, start=1):
            c = ws.cell(row=HR, column=ci, value=h)
            c.font, c.fill, c.border = self.f_head, self.fill_head, BORDER
            c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            ws.column_dimensions[get_column_letter(ci)].width = widths[h]
        ws.row_dimensions[HR].height = 30
        main = ("BZ-", "UC-", "NFR-", "OQ-")
        r = HR
        for row, header, _ in rfp["items"]:
            r += 1
            rid = str(row[0]).strip()
            text = " ".join(map(str, row[1:]))
            ids = md.find_ids(text)
            pick = lambda p: ", ".join(sorted({i for i in ids if i.startswith(p)}))  # noqa: E731
            vals = {"RFP": rid, "要求（要約）": _short(_summary_value(row, header), 120),
                    "要件定義での扱い": _col_value(row, header, ("扱い",)),
                    "BZ": pick("BZ-"), "UC": pick("UC-"), "NFR": pick("NFR-"),
                    "その他の対応先": _other_targets(row, header, ids, rid, main), "OQ": pick("OQ-")}
            for ci, h in enumerate(heads, start=1):
                v = vals[h]
                c = ws.cell(row=r, column=ci, value=self.namer(v) if v else None)
                c.border, c.font = BORDER, (self.f_id if ci == 1 else self.f_body)
                c.alignment = Alignment(wrap_text=True, vertical="top")
                if (r - HR) % 2 == 0:
                    c.fill = self.fill_zebra
        last = max(r, HR + 1)
        col = {h: get_column_letter(i) for i, h in enumerate(heads, start=1)}
        empty = ",".join(f'${col[h]}{HR + 1}=""' for h in ("BZ", "UC", "NFR", "その他の対応先"))
        cond = f"AND({empty})"
        if has_handling:
            hc = f"${col['要件定義での扱い']}{HR + 1}"
            cond = f'AND({empty},' + ",".join(f'ISERROR(SEARCH("{k}",{hc}))' for k in ("対象外", "先送り", "棄却", "保留")) + ")"
        ws.conditional_formatting.add(f"A{HR + 1}:{get_column_letter(len(heads))}{last}", FormulaRule(formula=[cond], fill=PatternFill("solid", fgColor="FCE4D6")))
        _fit_rows(ws, HR + 1, last, len(heads))
        ws.freeze_panes = ws.cell(row=HR + 1, column=2)
        ws.auto_filter.ref = f"A{HR}:{get_column_letter(len(heads))}{last}"
        self._print(ws, HR)

    # ---------------------------------------------------------------- assemble
    def build(self, sources: dict[str, list], out_dir: Path) -> Path:
        x = self.prof["excel"]
        self.prof["_present"] = set(sources)
        self.namer = common.DocNamer(common.doc_names(self.prof, sources))
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


def _find_col(header: list[str], keys: tuple[str, ...]) -> int | None:
    for i, h in enumerate(header):
        if any(k in str(h) for k in keys):
            return i
    return None


def _col_value(row: list, header: list[str], keys: tuple[str, ...]) -> str:
    i = _find_col(header, keys)
    return str(row[i]).strip() if i is not None and i < len(row) and row[i] is not None else ""


SKIP_SUMMARY = ("ID", "区分", "出典", "判定", "扱い", "対応", "OQ", "理由", "論点", "仮", "優先", "MoSCoW", "採否", "ステータス", "状態")


def _summary_value(row: list, header: list[str]) -> str:
    """RFP 台帳の「要求の要約」列の値。見出しに「要約」→「要求」→「内容」を含む列を探し、
    無ければ分類・判定などを除いた列のうち平均文字数が最長の列を使う。"""
    for keys in (("要約",), ("要求",), ("内容",)):
        i = _find_col([("" if any(k in h for k in ("ID", "区分", "扱い", "対応")) else h) for h in header], keys)
        if i is not None and i < len(row):
            return str(row[i] or "")
    cand = [i for i, h in enumerate(header) if i and not any(k in h for k in SKIP_SUMMARY) and i < len(row)]
    return str(row[max(cand, key=lambda i: len(str(row[i] or "")))] or "") if cand else ""


def _other_targets(row: list, header: list[str], ids: list[str], self_id: str, main: tuple[str, ...]) -> str:
    """BZ・UC・NFR・OQ 以外の対応先。「対応」を含む列（対応 ID など）があればその記載から BZ/UC/NFR/OQ を除いた残り
    （ROLE・IF・本書の節など）を出す。無ければ行内の他の ID（OBJ・RFP 自身を除く）を出す。"""
    i = _find_col(header, ("対応",))
    if i is not None and i < len(row):
        out = []
        for tok in re.split(r"[、,，;；/／\n]+", str(row[i] or "")):
            tok = tok.strip()
            if not tok or tok in ("—", "-", "－", "なし"):
                continue
            if md.find_ids(tok) and all(x.startswith(main) for x in md.find_ids(tok)) and \
                    re.fullmatch(r"[\s、,（）()]*", md.ID_RE.sub("", tok)):
                continue  # BZ・UC・NFR・OQ だけの記載（それぞれの列に出る）
            out.append(tok)
        return "、".join(dict.fromkeys(out))
    rest = [x for x in ids if not x.startswith(main) and x != self_id and not x.startswith(("RFP-", "OBJ-"))]
    return ", ".join(sorted(set(rest)))


def _uc_exempt_reason(row: list, header: list[str], ledger_name: str, adopt: str) -> str:
    """UC を持たなくてよい BZ の理由（空文字 ＝ 理由なし ＝ 対応漏れの候補）。
    目的系の BZ（UC は手段系に付く）、先送り・保留・棄却の BZ、人の運用だけの業務手段。"""
    kind = _col_value(row, header, ("種別",))
    is_goal = "目的" in ledger_name.split("_", 1)[-1] or "目的" in kind or (
        _find_col(header, ("手段",)) is None and _find_col(header, ("目的", "OBJ")) is not None)
    if is_goal:
        return "目的系の要求（UC は手段系の BZ に付く）"
    for k in ("先送り", "保留", "棄却"):
        if adopt.startswith(k) or (k in adopt and "採用" not in adopt):
            return f"{k}のため UC を定義しない"
    if "業務" in kind and "IT" not in kind.upper():
        return "業務手段（人の運用。システム化しない）"
    return ""


def _fit_rows(ws, first: int, last: int, ncol: int, pt_per_line: float = 18.0) -> None:
    """折り返す行の高さを内容から見積もって設定する（Excel の PDF 化・印刷で折返し分が切れないように）。
    1 行の高さは和文 UI フォント（游ゴシック・メイリオ）の 10pt が 2 行以上で切れない値（18pt）。
    列幅は半角文字数の単位、全角は 2 文字分として数える。"""
    import unicodedata
    widths = [ws.column_dimensions[get_column_letter(c)].width or 8.43 for c in range(1, ncol + 1)]
    for r in range(first, last + 1):
        lines = 1
        for c in range(1, ncol + 1):
            v = ws.cell(row=r, column=c).value
            if v is None or str(v).startswith("="):
                continue
            usable = max(widths[c - 1] - 2, 2)
            n = 0
            for part in str(v).split("\n"):
                w = sum(2 if unicodedata.east_asian_width(ch) in "WFA" else 1 for ch in part)
                n += max(1, -(-int(w * 1.05) // int(usable)))
            lines = max(lines, n)
        ws.row_dimensions[r].height = max(15, lines * pt_per_line + 3)


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
