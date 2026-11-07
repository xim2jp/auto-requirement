#!/bin/bash
# update-project.sh - 既存案件のフレームワークを更新する補助スクリプト（v0.12.0 マニフェスト3分類対応）
# 使い方:
#   bash <FRAMEWORK_ROOT>/scripts/update-project.sh [案件パス] [--auto]
#   --auto : 対話なしで安全な更新のみ適用（export-to-projects.sh からの一括配布用）
#
# 3分類（.claude-manifest = 前回配布時のハッシュ台帳を基準点にする。compatibility-contract.md 準拠）:
#   SAFE_UPDATE : 案件が未カスタマイズ & 本体が更新     → 上書き
#   CUSTOM_KEEP : 案件がカスタマイズ済 & 本体は未変更   → 保持
#   CONFLICT    : 両方が変更                             → 保持してレポートに列挙（手動マージ）
#   NEW         : 本体にのみ存在                         → 追加
#   （案件独自の追加ファイルは常に保持）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT_PATH="."
AUTO=0
for arg in "$@"; do
  case "$arg" in
    --auto) AUTO=1 ;;
    *) PROJECT_PATH="$arg" ;;
  esac
done

cd "$PROJECT_PATH"
PROJECT_PATH=$(pwd)

echo "🔄 フレームワーク更新"
echo "  対象案件: $PROJECT_PATH"
echo ""

if [ ! -f ".framework-version" ]; then
  echo "❌ .framework-version が見つかりません。フレームワークが導入されていない可能性があります"
  exit 1
fi

CURRENT_VERSION=$(head -n 1 .framework-version | tr -d ' ')
LATEST_VERSION=$(head -n 1 "$FRAMEWORK_ROOT/templates/project-init/.framework-version" | tr -d ' ')

echo "  現在のバージョン: $CURRENT_VERSION"
echo "  最新のバージョン: $LATEST_VERSION"
echo ""

if [ "$CURRENT_VERSION" = "$LATEST_VERSION" ]; then
  echo "✅ 既に最新版です"
  exit 0
fi

# バックアップ
BACKUP_DIR=".claude.backup.$(date +%Y%m%d_%H%M%S)"
echo "💾 現在の .claude/ を $BACKUP_DIR にバックアップ..."
cp -r .claude "$BACKUP_DIR"
echo "✅ バックアップ完了"
echo ""

# ---- マニフェスト読み込み（無ければ差分ファイルはすべて CONFLICT 扱いの保守的動作） ----
HAS_MANIFEST=0
declare -A BASE_HASH
if [ -f ".claude-manifest" ]; then
  HAS_MANIFEST=1
  while read -r hash path; do
    BASE_HASH["$path"]="$hash"
  done < <(grep -E '^[0-9a-f]{64}' .claude-manifest)
  echo "📒 .claude-manifest を読み込み（基準バージョン: $(grep '^version:' .claude-manifest | awk '{print $2}')）"
else
  echo "⚠️  .claude-manifest がありません（v0.12.0 より前の導入）。"
  echo "    カスタマイズ検出ができないため、差分のあるファイルはすべて CONFLICT 扱いにします"
fi
echo ""

REPORT=".claude-update-report-$(date +%Y%m%d_%H%M%S).md"
SAFE=0; KEEP=0; CONFLICT=0; NEW=0; SAME=0
CONFLICT_LIST=""
KEEP_LIST=""

hash_of() { sha256sum "$1" 2>/dev/null | awk '{print $1}'; }

# ---- 本体側の全ファイルを分類 ----
while IFS= read -r fw_file; do
  rel="${fw_file#$FRAMEWORK_ROOT/}"
  fw_hash=$(hash_of "$fw_file")
  if [ ! -f "$rel" ]; then
    mkdir -p "$(dirname "$rel")"
    cp "$fw_file" "$rel"
    NEW=$((NEW+1))
    continue
  fi
  proj_hash=$(hash_of "$rel")
  if [ "$proj_hash" = "$fw_hash" ]; then
    SAME=$((SAME+1))
    continue
  fi
  base="${BASE_HASH[$rel]:-}"
  if [ "$HAS_MANIFEST" = "1" ] && [ "$proj_hash" = "$base" ]; then
    # 案件は未カスタマイズ、本体が更新 → 安全に上書き
    cp "$fw_file" "$rel"
    SAFE=$((SAFE+1))
  elif [ "$HAS_MANIFEST" = "1" ] && [ "$fw_hash" = "$base" ]; then
    # 案件がカスタマイズ、本体は未変更 → 保持
    KEEP=$((KEEP+1)); KEEP_LIST="$KEEP_LIST- $rel\n"
  else
    # 両方変更（またはマニフェスト無し）→ 保持して要マージ
    CONFLICT=$((CONFLICT+1)); CONFLICT_LIST="$CONFLICT_LIST- $rel\n"
  fi
done < <(find "$FRAMEWORK_ROOT/.claude" -type f)

# ---- レポート ----
{
  echo "# フレームワーク更新レポート"
  echo ""
  echo "- 日時: $(date '+%Y-%m-%d %H:%M')"
  echo "- $CURRENT_VERSION → $LATEST_VERSION / バックアップ: $BACKUP_DIR"
  echo ""
  echo "| 分類 | 件数 | 意味 |"
  echo "|------|------|------|"
  echo "| SAFE_UPDATE | $SAFE | 未カスタマイズ＆本体更新 → 上書き適用済み |"
  echo "| NEW | $NEW | 本体の新規ファイル → 追加済み |"
  echo "| UP-TO-DATE | $SAME | 差分なし |"
  echo "| CUSTOM_KEEP | $KEEP | 案件カスタマイズを保持（本体は未変更） |"
  echo "| CONFLICT | $CONFLICT | 両方が変更 → 案件版を保持。**手動マージ判断が必要** |"
  echo ""
  if [ "$CONFLICT" -gt 0 ]; then
    echo "## ⚠️ CONFLICT（要マージ判断）"
    echo ""
    printf "%b" "$CONFLICT_LIST"
    echo ""
    echo "各ファイルについて本体版と案件版を diff し、本体の改善を取り込むか判断してください。"
    echo "カスタマイズが汎用的なら PROJECT_LEARNINGS.md 経由で本体へ還流を検討。"
    echo ""
  fi
  if [ "$KEEP" -gt 0 ]; then
    echo "## CUSTOM_KEEP（保持したカスタマイズ）"
    echo ""
    printf "%b" "$KEEP_LIST"
  fi
} > "$REPORT"

echo "📊 適用結果: SAFE_UPDATE=$SAFE / NEW=$NEW / UP-TO-DATE=$SAME / CUSTOM_KEEP=$KEEP / CONFLICT=$CONFLICT"
echo "📝 レポート: $REPORT"

# ---- バージョン記録とマニフェスト再生成 ----
finalize() {
  echo "$LATEST_VERSION" > .framework-version
  {
    echo "# .claude-manifest — フレームワーク配布ファイルのハッシュ台帳（compatibility-contract.md 準拠）"
    echo "# update-project.sh がカスタマイズ検出（3分類）に使用する。手動編集しない"
    echo "version: $LATEST_VERSION"
    (cd "$FRAMEWORK_ROOT" && find .claude -type f | LC_ALL=C sort | xargs -d '\n' sha256sum)
  } > .claude-manifest
  echo "✅ .framework-version / .claude-manifest を $LATEST_VERSION に更新"
}

if [ "$AUTO" = "1" ]; then
  finalize
  echo ""
  echo "✅ 自動更新完了（CONFLICT は保持済み。レポートを確認してください）"
  exit 0
fi

echo ""
if [ "$CONFLICT" -gt 0 ]; then
  echo "CONFLICT が $CONFLICT 件あります。選択してください:"
  echo "  1) このまま確定（案件版を保持。後でレポートを見ながら手動マージ）【推奨】"
  echo "  2) CONFLICT も本体版で全上書き（案件カスタマイズは $BACKUP_DIR から復元可能）"
  echo "  3) 中止（バックアップから復元）"
  read -p "選択 (1/2/3): " choice
  case $choice in
    1) finalize ;;
    2)
      printf "%b" "$CONFLICT_LIST" | sed 's/^- //' | while read -r rel; do
        [ -n "$rel" ] && cp "$FRAMEWORK_ROOT/$rel" "$rel"
      done
      finalize
      echo "✅ CONFLICT も本体版で上書きしました"
      ;;
    3)
      rm -rf .claude && mv "$BACKUP_DIR" .claude && rm -f "$REPORT"
      echo "↩️ 復元して中止しました"
      exit 0
      ;;
    *) echo "無効な選択。SAFE_UPDATE/NEW は適用済みのため、このまま確定します"; finalize ;;
  esac
else
  finalize
fi

echo ""
echo "📝 PROJECT_LEARNINGS.md も確認して、適用済みの還流が含まれているか確認してください"
