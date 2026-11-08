"""check.py — 生成した Office 成果物の機械検査。結果を docs/04-deliverables/check-report.md に書く。

FAIL（exit 1）：ファイルが無い・開けない／Word に目次・ヘッダー・フッターが無い／台帳の件数が Markdown と不一致
WARN：テンプレの書きかけ（YYYY-MM-DD・〈〉など）／社内用語の混入（エージェント名・Phase・docs/ パス）／
      未定義 ID の参照／UC を持たない BZ／スライドの文字あふれ懸念
"""
from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pptx import Presentation

import common
import mdparse as md
from profile import out_name
from xlsx_builder import ExcelBuilder, sheet_label

INTERNAL = re.compile(
    r"requirements-architect|requirements-reviewer|project-manager|office-document-producer|deliverable-reviewer|"
    r"Self-Check|Handoff|\bPhase \d|docs/0\d-|\.claude/|htmldocs|status\.md|RETURN_TO|VERDICT:"
)
PLACEHOLDER = re.compile(r"YYYY-MM-DD|YYYY-MM|〈[^〉]{0,20}〉|（記入）|（未記入）|\bTODO\b|\bTBD\b|¥…|… 時間|N 件|（…）")


def _docx_text(doc) -> list[str]:
    out = [p.text for p in doc.paragraphs]
    for t in doc.tables:
        for row in t.rows:
            for c in row.cells:
                out.append(c.text)
    return out


def _scan(lines: list[str], where: str, warn: list[str], limit: int = 8):
    ph, it = [], []
    for s in lines:
        if not s:
            continue
        for m in PLACEHOLDER.finditer(s):
            ph.append(m.group(0))
        for m in INTERNAL.finditer(s):
            it.append(m.group(0))
    if ph:
        uniq = sorted(set(ph))
        warn.append(f"{where}：書きかけ表記 {len(ph)} 箇所（{', '.join(uniq[:limit])}）")
    if it:
        uniq = sorted(set(it))
        warn.append(f"{where}：社内用語・作業用パスの混入 {len(it)} 箇所（{', '.join(uniq[:limit])}）")


def run(prof: dict, root: Path, sources: dict, out_dir: Path, build_stats: dict | None = None) -> tuple[str, Path]:
    fail: list[str] = []
    warn: list[str] = []
    info: list[str] = []

    # ---------------- Word（RFP・要件定義書・別紙。docx_builder.plan と同じ一覧を検査する）
    import docx_builder  # noqa: PLC0415（循環を避けて遅延 import）
    for spec in docx_builder.plan(prof, sources):
        sp = prof
        if spec.get("issuer") == "client" and spec["main"] in sources:  # RFP は正本の版数でファイル名が付く
            sp = {**prof, "project": docx_builder.client_project(prof, sources[spec["main"]], spec)}
        p = out_dir / out_name(sp, spec["kind"], "docx")
        label = f"Word「{spec['kind']}」"
        if not p.exists():
            fail.append(f"{label} が無い：{p.name}")
            continue
        try:
            doc = Document(p)
            xml = doc.element.xml
            if "TOC \\o" not in xml:
                fail.append(f"{label}：目次フィールドが無い")
            sec = doc.sections[-1]
            if not sec.footer.paragraphs or "PAGE" not in sec.footer._element.xml:
                fail.append(f"{label}：フッターにページ番号が無い")
            heads = [x for x in doc.paragraphs if x.style.name.startswith("Heading")]
            info.append(f"{label}：見出し {len(heads)}・表 {len(doc.tables)}・セクション {len(doc.sections)}")
            _scan(_docx_text(doc), label, warn)
        except Exception as e:  # noqa: BLE001
            fail.append(f"{label} が開けない：{e}")

    # ---------------- Excel
    if prof["excel"].get("enabled", True):
        p = out_dir / out_name(prof, prof["excel"]["kind"], "xlsx")
        if not p.exists():
            fail.append(f"Excel が無い：{p.name}")
        else:
            try:
                wb = load_workbook(p)
                all_text = []
                for spec in prof["excel"].get("sheets", []):
                    blocks = sources.get(spec["source"])
                    if not blocks:
                        continue
                    gs = ExcelBuilder.groups(blocks, spec)
                    for label, _, rows in gs:
                        name = spec["name"][:31] if len(gs) == 1 else sheet_label(spec["name"], label)
                        if name not in wb.sheetnames:
                            fail.append(f"Excel：シート「{name}」が無い（{spec['source']} に {len(rows)} 件あり）")
                            continue
                        ws = wb[name]
                        n = sum(1 for r in ws.iter_rows(min_row=5, max_col=1, values_only=True) if r[0] not in (None, ""))
                        if n != len(rows):
                            fail.append(f"Excel：「{name}」{n} 件 ≠ Markdown {len(rows)} 件")
                for ws in wb.worksheets:
                    for row in ws.iter_rows(values_only=True):
                        all_text += [str(v) for v in row if isinstance(v, str) and not v.startswith("=")]
                info.append(f"Excel：シート {len(wb.sheetnames)}（{'・'.join(wb.sheetnames)}）")
                _scan(all_text, "Excel", warn)
            except Exception as e:  # noqa: BLE001
                fail.append(f"Excel が開けない：{e}")

    # ---------------- PowerPoint
    if prof["powerpoint"].get("enabled", True):
        p = out_dir / out_name(prof, prof["powerpoint"]["kind"], "pptx")
        if not p.exists():
            fail.append(f"PowerPoint が無い：{p.name}")
        else:
            try:
                prs = Presentation(p)
                texts = []
                for s in prs.slides:
                    for sh in s.shapes:
                        if sh.has_text_frame:
                            texts.append(sh.text_frame.text)
                        if getattr(sh, "has_table", False) and sh.has_table:
                            for row in sh.table.rows:
                                texts += [c.text for c in row.cells]
                info.append(f"PowerPoint：スライド {len(prs.slides)} 枚")
                _scan(texts, "PowerPoint", warn)
            except Exception as e:  # noqa: BLE001
                fail.append(f"PowerPoint が開けない：{e}")
        for w in (build_stats or {}).get("pptx", {}).get("warnings", []):
            warn.append(f"PowerPoint：{w}")

    # ---------------- ID 整合（Markdown 正本どうし）
    defined: set[str] = set()
    for blocks in sources.values():
        for _, tb in md.iter_tables_with_context(blocks):
            for r in tb.rows_text():
                if r and re.fullmatch(md.ID_RE.pattern, r[0].strip()):
                    defined.add(r[0].strip())
        for b in blocks:
            if isinstance(b, md.Heading):
                m = md.ID_RE.match(b.text.strip())
                if m:
                    defined.add(m.group(0))
    referenced: dict[str, set[str]] = {}
    for name, blocks in sources.items():
        text = common.SOURCE_PATHS[name].read_text(encoding="utf-8")
        for i in set(md.find_ids(text)):
            referenced.setdefault(i, set()).add(name)
    known_prefixes = {i.rsplit("-", 1)[0].split("-")[0] for i in defined}
    undefined = sorted(i for i in referenced if i not in defined and i.split("-")[0] in known_prefixes)
    if undefined:
        warn.append(f"未定義 ID の参照 {len(undefined)} 件：{', '.join(undefined[:15])}{' …' if len(undefined) > 15 else ''}")
    xs = (build_stats or {}).get("xlsx", {})
    if "bz_without_uc_gap" in xs:  # 目的系・先送り・保留・棄却・業務手段は Excel に理由付きで灰色表示される
        gap, exc = xs.get("bz_without_uc_gap") or [], xs.get("bz_without_uc_excused") or {}
        if gap:
            warn.append(f"UC を持たない採用 BZ {len(gap)} 件（対応漏れの候補）：{', '.join(gap)}")
        if exc:
            info.append(f"UC を持たない BZ のうち理由のあるもの {len(exc)} 件（Excel トレーサビリティに理由を表示）：{', '.join(exc)}")
    elif xs.get("bz_without_uc"):
        bz_wo = xs["bz_without_uc"]
        warn.append(f"UC を持たない BZ {len(bz_wo)} 件（業務手段のみの BZ なら問題なし）：{', '.join(bz_wo)}")
    if (build_stats or {}).get("docx", {}).get("mermaid_source"):
        warn.append(f"Mermaid 図 {build_stats['docx']['mermaid_source']} 件をソース枠で掲載（mmdc を導入すると図になる）")

    verdict = "FAIL" if fail else ("WARN" if warn else "PASS")
    report = root / "docs/04-deliverables/check-report.md"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Office 成果物 機械検査レポート", "",
        f"- 実行日時：{dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- 対象：{out_dir.relative_to(root) if out_dir.is_relative_to(root) else out_dir}/",
        f"- 判定：**{verdict}**（FAIL {len(fail)}／WARN {len(warn)}）", "",
        "## FAIL", *(f"- {x}" for x in fail or ["なし"]), "",
        "## WARN", *(f"- {x}" for x in warn or ["なし"]), "",
        "## 情報", *(f"- {x}" for x in info), "",
        "> 機械検査は形式の確認だけを行う。内容・体裁の判断は deliverable-reviewer が行う。",
    ]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return verdict, report
