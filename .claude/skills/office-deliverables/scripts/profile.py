"""profile.py — 成果物プロファイル（docs/04-deliverables/deliverable-profile.yaml）の読み込みと既定値。"""
from __future__ import annotations

import copy
import datetime as dt
from pathlib import Path

import yaml

DEFAULTS: dict = {
    "project": {
        "name": "（案件名）",
        "client": "（発注者名）",
        "vendor": "（作成者・受注者名）",
        "doc_number": "",
        "version": "1.0",
        "status": "初版",
        "date": None,  # None = 今日
        "confidentiality": "社外秘",
        "author": "",
        "approvals": [  # 承認欄（表紙の次ページ）
            {"role": "作成", "name": "", "date": ""},
            {"role": "確認", "name": "", "date": ""},
            {"role": "承認", "name": "", "date": ""},
        ],
        "revisions": [],  # [{version, date, description, author}]
    },
    "theme": {
        "primary": "1F3864",   # 見出し・表ヘッダー
        "accent": "2E75B6",    # 強調・罫線
        "light": "DEEAF6",     # 表の縞・注記の背景
        "muted": "595959",     # 補助テキスト
        "font_body": "游明朝",
        "font_heading": "游ゴシック",
        "font_latin_body": "Century",
        "font_latin_heading": "Arial",
        "font_ui": "游ゴシック",     # Excel・PowerPoint
        "font_code": "BIZ UDゴシック",
    },
    "output": {
        "dir": "deliverables",
        "filename_pattern": "{kind}_{project}_v{version}",
        "strip_internal_sections": ["Self-Check", "Handoff", "セルフレビュー"],
        "strip_heading_emoji": True,
        "mermaid": "auto",  # auto: mmdc があれば画像化 / source: ソース枠で掲載 / off: 省略
    },
    "word": {
        "enabled": True,
        "kind": "要件定義書",
        "title": "要件定義書",
        "subtitle": "",
        "landscape_table_columns": 8,  # この列数以上の表は横向きページに置く
        "main": "requirements.md",
        "appendices": [
            {"title": "業務要件一覧", "source": "business-requirements.md"},
            {"title": "ユースケース一覧", "source": "use-cases.md"},
            {"title": "非機能要件一覧", "source": "non-functional.md"},
            {"title": "ロール・権限マトリクス", "source": "permissions-matrix.md"},
            {"title": "用語集", "source": "glossary.md"},
            {"title": "要確認事項一覧", "source": "open-questions.md"},
            {"title": "RFP 要求分析表", "source": "rfp-analysis.md"},
        ],
    },
    "excel": {
        "enabled": True,
        "kind": "要件一覧",
        "title": "要件一覧（管理台帳）",
        "sheets": [
            {"name": "達成目標(OBJ)", "source": "rfp-analysis.md", "id_prefix": "OBJ-"},
            {"name": "RFP要求", "source": "rfp-analysis.md", "id_prefix": "RFP-"},
            {"name": "業務要件(BZ)", "source": "business-requirements.md", "id_prefix": "BZ-"},
            {"name": "ユースケース(UC)", "source": "use-cases.md", "id_prefix": "UC-", "first_table_only": True},
            {"name": "非機能要件(NFR)", "source": "non-functional.md", "id_prefix": "NFR-"},
            {"name": "ロール(ROLE)", "source": "permissions-matrix.md", "id_prefix": "ROLE-", "first_table_only": True},
            {"name": "外部IF", "source": "requirements.md", "id_prefix": "IF-"},
            {"name": "ステークホルダ", "source": "requirements.md", "id_prefix": "SH-"},
            {"name": "用語集", "source": "glossary.md", "id_prefix": "TERM-"},
            {"name": "要確認事項(OQ)", "source": "open-questions.md", "id_prefix": "OQ-"},
            {"name": "決定ログ", "source": "decision-log.md", "id_prefix": "D-"},
        ],
        "traceability": True,
        "summary": True,
    },
    "powerpoint": {
        "enabled": True,
        "kind": "要件定義サマリー",
        "spec": "summary-deck.yaml",  # docs/04-deliverables/ からの相対。無ければ自動構成
        "max_table_rows": 9,
    },
}


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load(root: Path, profile_path: Path | None = None) -> dict:
    path = profile_path or root / "docs/04-deliverables/deliverable-profile.yaml"
    data = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    prof = _deep_merge(DEFAULTS, data)
    p = prof["project"]
    if not p.get("date"):
        p["date"] = dt.date.today().isoformat()
    p["date"] = str(p["date"])
    if not p.get("revisions"):
        p["revisions"] = [{"version": p["version"], "date": p["date"], "description": p.get("status") or "初版", "author": p.get("author") or p.get("vendor")}]
    prof["_profile_path"] = str(path) if path.exists() else None
    return prof


def out_name(prof: dict, kind: str, ext: str) -> str:
    p = prof["project"]
    name = prof["output"]["filename_pattern"].format(kind=kind, project=p["name"], version=p["version"], date=p["date"].replace("-", ""))
    for ch in '\\/:*?"<>|':
        name = name.replace(ch, "_")
    return f"{name}.{ext}"


def hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
