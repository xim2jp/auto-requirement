#!/bin/bash
# smoke-test.sh - 配布物が「そのまま動く」かを通しで確かめる。
#   new-project.sh → setup.sh（.venv 作成）→ テンプレートを RFP・要件定義の正本として配置 → build.sh extract / all → 機械検査
# CI（framework-checks.yml）とリリース前の手元確認で使う。失敗は exit 1。
# 使い方: bash scripts/smoke-test.sh [作業ディレクトリ]（省略時は一時ディレクトリ。終了時に削除）

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
KEEP=0
if [ -n "$1" ]; then WORK="$1"; KEEP=1; rm -rf "$WORK"; else WORK="$(mktemp -d)/smoke-project"; fi
cleanup() { [ "$KEEP" = "1" ] || rm -rf "$(dirname "$WORK")"; }
trap cleanup EXIT

echo "🧪 スモークテスト: $WORK"
printf '\n' | bash "$ROOT/scripts/new-project.sh" "$WORK" > /tmp/smoke-new-project.log 2>&1 || { cat /tmp/smoke-new-project.log; exit 1; }
cd "$WORK"
for p in .claude/agents/project-manager.md .claude/skills/office-deliverables/scripts/build.sh docs/00-inputs/README.md docs/99-pm/status.md docs/04-deliverables/deliverable-profile.yaml .venv/bin/python; do
  [ -e "$p" ] || { echo "❌ $p がありません"; exit 1; }
done
echo "✅ new-project.sh / setup.sh"

T=.claude/skills/requirements-toolkit/templates
mkdir -p docs/01-rfp docs/03-requirements
cp "$T/rfp.md" docs/00-inputs/rfp.md
cp "$T/rfp-analysis.md" docs/01-rfp/rfp-analysis.md 2>/dev/null || true
cp .claude/skills/rfp-authoring/templates/rfp-document.md docs/01-rfp/rfp.md   # 構想から作った RFP の代わり
cp "$T/requirements-doc.md" docs/03-requirements/requirements.md
for f in business-requirements use-cases non-functional permissions-matrix glossary open-questions decision-log; do
  cp "$T/$f.md" docs/03-requirements/
done
cp .claude/skills/office-deliverables/templates/summary-deck.yaml docs/04-deliverables/summary-deck.yaml

bash .claude/skills/office-deliverables/scripts/build.sh extract
bash .claude/skills/office-deliverables/scripts/build.sh all
for g in "要件定義要求書_*.docx" "要件定義書_*.docx" "別紙1_*.docx" "別紙7_*.docx" "要件一覧_*.xlsx" "要件定義サマリー_*.pptx"; do
  ls deliverables/$g >/dev/null 2>&1 || { echo "❌ 納品物がありません：$g"; ls deliverables; exit 1; }
done
grep -q '判定：\*\*FAIL' docs/04-deliverables/check-report.md && { cat docs/04-deliverables/check-report.md; exit 1; }
echo "✅ Office 納品物を生成：要件定義要求書・要件定義書・別紙 7・要件一覧・サマリー（機械検査 FAIL 0。テンプレのため WARN は想定内）"
echo "🎉 スモークテスト成功"
