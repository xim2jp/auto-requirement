#!/bin/bash
# collect-learnings.sh - 各案件のPROJECT_LEARNINGS.mdを集約する補助スクリプト
# 使い方: bash scripts/collect-learnings.sh [案件ディレクトリの親フォルダ]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# デフォルトは ~/projects
PROJECTS_DIR="${1:-$HOME/projects}"

echo "🔍 案件LEARNINGS集約"
echo "  検索ディレクトリ: $PROJECTS_DIR"
echo ""

if [ ! -d "$PROJECTS_DIR" ]; then
  echo "❌ ディレクトリが見つかりません: $PROJECTS_DIR"
  exit 1
fi

# 出力先
YEAR_MONTH=$(date +%Y-%m)
OUTPUT_FILE="$FRAMEWORK_ROOT/docs/learnings/$YEAR_MONTH-collected.md"
mkdir -p "$FRAMEWORK_ROOT/docs/learnings"

# 集約開始
cat > "$OUTPUT_FILE" << EOF
# Collected Learnings: $YEAR_MONTH

集約日時: $(date +"%Y-%m-%d %H:%M:%S")
集約元: $PROJECTS_DIR

---

EOF

PROJECT_COUNT=0

# .framework-version があるディレクトリを案件とみなす
for dir in "$PROJECTS_DIR"/*/; do
  if [ -f "$dir/.framework-version" ] && [ -f "$dir/PROJECT_LEARNINGS.md" ]; then
    PROJECT_NAME=$(basename "$dir")
    FRAMEWORK_VER=$(cat "$dir/.framework-version" | head -n 1 | tr -d ' ')
    # 最終更新日を取得（GNU/Linux を優先し、失敗したら BSD/macOS 形式にフォールバック）
    if LAST_UPDATED=$(stat -c "%y" "$dir/PROJECT_LEARNINGS.md" 2>/dev/null); then
      LAST_UPDATED=${LAST_UPDATED%% *}
    else
      LAST_UPDATED=$(stat -f "%Sm" -t "%Y-%m-%d" "$dir/PROJECT_LEARNINGS.md" 2>/dev/null)
    fi
    
    echo "📄 集約中: $PROJECT_NAME ($FRAMEWORK_VER)"
    
    cat >> "$OUTPUT_FILE" << EOF

## 案件: $PROJECT_NAME

- フレームワーク版: $FRAMEWORK_VER
- LEARNINGS最終更新: $LAST_UPDATED
- パス: $dir

\`\`\`markdown
EOF
    cat "$dir/PROJECT_LEARNINGS.md" >> "$OUTPUT_FILE"
    cat >> "$OUTPUT_FILE" << EOF
\`\`\`

---

EOF
    PROJECT_COUNT=$((PROJECT_COUNT + 1))
  fi
done

if [ $PROJECT_COUNT -eq 0 ]; then
  echo "⚠️  フレームワークを使った案件が見つかりませんでした"
  rm -f "$OUTPUT_FILE"
  exit 1
fi

echo ""
echo "✅ 集約完了"
echo "  案件数: $PROJECT_COUNT"
echo "  出力先: $OUTPUT_FILE"
echo ""
echo "次のステップ:"
echo "  1. $OUTPUT_FILE を開いて確認"
echo "  2. 還流候補を抽出"
echo "  3. GitHub Issue を作成（テンプレ: framework-improvement.md）"
