#!/bin/bash
# export-to-projects.sh - フレームワーク最新版を登録済み派生システムへ一括配布する（v0.12.0）
# 使い方:
#   bash scripts/export-to-projects.sh            # 全登録案件へ配布（update-project.sh --auto）
#   bash scripts/export-to-projects.sh --dry-run  # 配布対象と現在バージョンの確認のみ
#
# 配布先は docs/projects/INDEX.md の「配布先ローカルパス」節（EXPORT-TARGETS マーカー内）から読む。
# 適用は update-project.sh の3分類（SAFE_UPDATE/CUSTOM_KEEP/CONFLICT。案件カスタマイズは保持）。

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
REGISTRY="$FRAMEWORK_ROOT/docs/projects/INDEX.md"
LATEST_VERSION=$(head -n 1 "$FRAMEWORK_ROOT/templates/project-init/.framework-version" | tr -d ' ')
DRY_RUN=0
[ "$1" = "--dry-run" ] && DRY_RUN=1

echo "📦 フレームワーク一括配布（$LATEST_VERSION）"
echo ""

# EXPORT-TARGETS-START/END の間から「名前<空白>パス」行を抽出
TARGETS=$(sed -n '/EXPORT-TARGETS-START/,/EXPORT-TARGETS-END/p' "$REGISTRY" \
  | grep -vE '^\s*(#|<!--|$)' | grep -vE 'EXPORT-TARGETS' || true)

if [ -z "$TARGETS" ]; then
  echo "⚠️ 配布先が登録されていません。"
  echo "   docs/projects/INDEX.md の「配布先ローカルパス」節に以下の形式で追記してください:"
  echo "   my-saas-project    ~/projects/my-saas-project"
  exit 0
fi

LOG="$FRAMEWORK_ROOT/docs/projects/export-log.md"
[ -f "$LOG" ] || printf "# 配布ログ（export-to-projects.sh）\n\n| 日時 | バージョン | 案件 | 結果 | CONFLICT |\n|------|-----------|------|------|----------|\n" > "$LOG"

OK=0; NG=0
while read -r name path; do
  [ -z "$name" ] && continue
  path="${path/#\~/$HOME}"
  echo "── $name（$path）"
  if [ ! -d "$path" ]; then
    echo "   ❌ ディレクトリが存在しません。スキップ"
    NG=$((NG+1))
    [ "$DRY_RUN" = "0" ] && echo "| $(date '+%Y-%m-%d %H:%M') | $LATEST_VERSION | $name | ❌ パス不在 | - |" >> "$LOG"
    continue
  fi
  CUR=$(head -n 1 "$path/.framework-version" 2>/dev/null | tr -d ' ' || echo "unknown")
  echo "   現在: $CUR → 配布: $LATEST_VERSION"
  if [ "$DRY_RUN" = "1" ]; then
    continue
  fi
  if OUTPUT=$(bash "$SCRIPT_DIR/update-project.sh" "$path" --auto 2>&1); then
    SUMMARY=$(echo "$OUTPUT" | grep '📊 適用結果' | sed 's/📊 適用結果: //' || echo "-")
    CONFLICTS=$(echo "$SUMMARY" | grep -oE 'CONFLICT=[0-9]+' | cut -d= -f2 || echo 0)
    echo "   ✅ $SUMMARY"
    echo "| $(date '+%Y-%m-%d %H:%M') | $LATEST_VERSION | $name | ✅ $SUMMARY | ${CONFLICTS:-0} |" >> "$LOG"
    OK=$((OK+1))
  else
    echo "   ❌ 更新失敗:"
    echo "$OUTPUT" | tail -5 | sed 's/^/      /'
    echo "| $(date '+%Y-%m-%d %H:%M') | $LATEST_VERSION | $name | ❌ 失敗 | - |" >> "$LOG"
    NG=$((NG+1))
  fi
done <<< "$TARGETS"

echo ""
if [ "$DRY_RUN" = "1" ]; then
  echo "🔍 dry-run 完了（変更なし）"
else
  echo "🎉 配布完了: 成功 $OK / 失敗 $NG"
  echo "📝 ログ: docs/projects/export-log.md"
  echo "⚠️ CONFLICT が出た案件は、案件側の .claude-update-report-*.md を確認して手動マージ判断をしてください"
fi
