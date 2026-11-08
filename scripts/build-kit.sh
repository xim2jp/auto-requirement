#!/bin/bash
# build-kit.sh - 配布用 ZIP キット（dist/rfp-requirements-kit-v<版>.zip）を作る。
#   中身は「new-project.sh で作った直後の案件」から README.md・setup.sh・.venv などを除いたもの。
#   利用者は README.md だけのリポジトリの直下に解凍し、Claude Code に作りたいシステムのことを話しかけるだけでよい（RFP があれば docs/00-inputs/ に置く）。
# 使い方: bash scripts/build-kit.sh [--test]
#   --test : README.md だけのダミーリポジトリに解凍し、テンプレートを正本にして Office 生成まで通す

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION="$(head -n1 "$ROOT/templates/project-init/.framework-version" | tr -d ' ')"
NAME="rfp-requirements-kit-v$VERSION"
OUT="$ROOT/dist/$NAME.zip"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

echo "📦 $NAME を作成"
SKIP_VENV=1 bash "$ROOT/scripts/new-project.sh" "$WORK/kit" < /dev/null > "$WORK/new-project.log" 2>&1 \
  || { cat "$WORK/new-project.log"; exit 1; }

cd "$WORK/kit"
# 利用者のリポジトリに不要なもの（README.md は利用者のものを残すため同梱しない）
rm -rf setup.sh scripts tmp .venv .mcp.json.example README.md
find . -name __pycache__ -type d -prune -exec rm -rf {} +
# 導入日は利用者側で決まるので、作成日の日付を伏せる
TODAY="$(date +%Y-%m-%d)"
sed -i "s/$TODAY/（導入日）/g" docs/99-pm/status.md
# tmp/ は build.sh が作る。空の docs/ フォルダは .gitkeep で残る
# 非エンジニア向けの「はじめに」（README.md は利用者のものなので別名で置く）
cp "$ROOT/templates/kit/START_HERE.md" START_HERE.md

mkdir -p "$ROOT/dist"
rm -f "$OUT"
# zip コマンドに依存しない（Python 標準ライブラリで作る。空フォルダも項目として入れる）
python3 - "$OUT" <<'PY'
import os, sys, zipfile
out = sys.argv[1]; n = 0
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for d, dirs, files in os.walk("."):
        dirs.sort()
        rel = os.path.relpath(d, ".")
        if rel != "." and not files and not dirs:
            z.writestr(rel.replace(os.sep, "/") + "/", "")
        for f in sorted(files):
            if f == ".DS_Store":
                continue
            z.write(os.path.join(d, f), os.path.normpath(os.path.join(rel, f)).replace(os.sep, "/")); n += 1
tops = sorted({i.split("/")[0] + ("/" if "/" in i else "") for i in zipfile.ZipFile(out).namelist()})
print(f"✅ {out}（{n} ファイル、{os.path.getsize(out)//1024} KB）")
print("   直下：" + "  ".join(tops))
PY

if [ "$1" = "--test" ]; then
  echo ""
  echo "🧪 README.md だけのリポジトリに解凍して確認"
  T="$WORK/user-repo"; mkdir -p "$T"; echo "# my-repo" > "$T/README.md"
  cd "$T" && python3 -m zipfile -e "$OUT" .
  [ "$(head -1 README.md)" = "# my-repo" ] || { echo "❌ README.md が上書きされた"; exit 1; }
  for p in START_HERE.md CLAUDE.md .claude/agents/rfp-writer.md .claude/settings.json .claude/agents/project-manager.md docs/00-inputs/README.md docs/99-pm/status.md docs/04-deliverables/deliverable-profile.yaml .gitignore; do
    [ -e "$p" ] || { echo "❌ $p がありません"; exit 1; }
  done
  S=.claude/skills/requirements-toolkit/templates
  cp "$S/rfp.md" docs/00-inputs/rfp.md
  cp "$S/rfp-analysis.md" docs/01-rfp/rfp-analysis.md
  cp .claude/skills/rfp-authoring/templates/rfp-document.md docs/01-rfp/rfp.md
  cp "$S/requirements-doc.md" docs/03-requirements/requirements.md
  for f in business-requirements use-cases non-functional permissions-matrix glossary open-questions decision-log; do cp "$S/$f.md" docs/03-requirements/; done
  bash .claude/skills/office-deliverables/scripts/build.sh all > "$WORK/build.log" 2>&1 || { cat "$WORK/build.log"; exit 1; }
  for g in "要件定義要求書_*.docx" "要件定義書_*.docx" "別紙1_*.docx" "別紙7_*.docx" "要件一覧_*.xlsx" "要件定義サマリー_*.pptx"; do
    ls deliverables/$g >/dev/null 2>&1 || { echo "❌ 納品物がありません：$g"; ls deliverables; exit 1; }
  done
  grep -q '判定：\*\*FAIL' docs/04-deliverables/check-report.md && { cat docs/04-deliverables/check-report.md; exit 1; }
  echo "✅ 解凍 → 初回の build.sh で Python 環境を自動作成 → 要件定義要求書・要件定義書・別紙・要件一覧・サマリーを生成（FAIL 0）"
  echo "🎉 キットのテスト成功"
fi
