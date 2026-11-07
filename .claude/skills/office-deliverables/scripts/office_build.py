#!/usr/bin/env python3
"""office_build.py — 要件定義の Markdown 正本（docs/03-requirements/）から Office 成果物を生成・検査する。

使い方（プロジェクトルートで。通常は build.sh 経由）:
  python office_build.py all            # Word・Excel・PowerPoint を生成し、機械検査まで行う
  python office_build.py docx|xlsx|pptx # 個別に生成
  python office_build.py check          # 生成済みファイルの機械検査だけ
オプション:
  --root DIR      プロジェクトルート（既定: カレント）
  --profile FILE  成果物プロファイル（既定: docs/04-deliverables/deliverable-profile.yaml）
  --out DIR       出力先（既定: プロファイルの output.dir = deliverables/）
  --pdf           LibreOffice（soffice）があれば PDF も書き出す
  --mermaid MODE  auto|npx|source|off（プロファイルの output.mermaid を上書き）
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check  # noqa: E402
import common  # noqa: E402
import docx_builder  # noqa: E402
import pptx_builder  # noqa: E402
import profile as profile_mod  # noqa: E402
import xlsx_builder  # noqa: E402


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", nargs="?", default="all", choices=["all", "docx", "xlsx", "pptx", "check"])
    ap.add_argument("--root", default=".")
    ap.add_argument("--profile")
    ap.add_argument("--out")
    ap.add_argument("--pdf", action="store_true")
    ap.add_argument("--mermaid", choices=["auto", "npx", "source", "off"])
    a = ap.parse_args(argv)

    root = Path(a.root).resolve()
    prof = profile_mod.load(root, Path(a.profile).resolve() if a.profile else None)
    if a.mermaid:
        prof["output"]["mermaid"] = a.mermaid
    out_dir = Path(a.out).resolve() if a.out else root / prof["output"]["dir"]
    sources = common.load_sources(root)
    if not sources:
        print("❌ docs/03-requirements/ に Markdown がありません。要件定義（Phase 2）を先に完了してください。", file=sys.stderr)
        return 2
    if not prof.get("_profile_path"):
        print("⚠️  deliverable-profile.yaml が無いため既定値（案件名・発注者が未設定）で生成します")

    stats: dict = {}
    made: list[Path] = []
    targets = ["docx", "xlsx", "pptx"] if a.target == "all" else ([] if a.target == "check" else [a.target])
    for t in targets:
        key = {"docx": "word", "xlsx": "excel", "pptx": "powerpoint"}[t]
        if not prof[key].get("enabled", True):
            continue
        mod = {"docx": docx_builder, "xlsx": xlsx_builder, "pptx": pptx_builder}[t]
        path, st = mod.build(prof, root, sources, out_dir)
        stats[t] = st
        made.append(path)
        print(f"✅ {path.relative_to(root) if path.is_relative_to(root) else path}")

    if a.pdf and made:
        soffice = shutil.which("soffice") or shutil.which("libreoffice")
        if soffice:
            for p in made:
                subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", str(out_dir), str(p)],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=300)
                print(f"📄 {p.with_suffix('.pdf').name}")
        else:
            print("⚠️  soffice が見つからないため PDF は省略しました")

    if stats:
        (root / "docs/04-deliverables").mkdir(parents=True, exist_ok=True)
        (root / "docs/04-deliverables/build-stats.json").write_text(
            json.dumps(stats, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    else:
        sp = root / "docs/04-deliverables/build-stats.json"
        if sp.exists():
            stats = json.loads(sp.read_text(encoding="utf-8"))

    if a.target in ("all", "check"):
        verdict, report = check.run(prof, root, sources, out_dir, stats)
        icon = {"PASS": "✅", "WARN": "⚠️ ", "FAIL": "❌"}[verdict]
        print(f"{icon} 機械検査 {verdict}：{report.relative_to(root)}")
        return 1 if verdict == "FAIL" else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
