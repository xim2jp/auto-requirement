#!/bin/bash
# gen-manifest.sh - .claude-manifest（配布時ハッシュ台帳）を生成する（v0.12.0）
# update-project.sh の3分類差分適用（SAFE_UPDATE / CUSTOM_KEEP / CONFLICT）の基準点になる。
# 使い方: プロジェクトルートで bash scripts/gen-manifest.sh
#   （フレームワーク導入・更新の直後に実行し、「配布された状態」のハッシュを記録する）

set -e

if [ ! -d ".claude" ]; then
  echo "❌ .claude/ が見つかりません。プロジェクトルートで実行してください"
  exit 1
fi

VERSION=$(head -n 1 .framework-version 2>/dev/null | tr -d ' ')
OUT=".claude-manifest"

{
  echo "# .claude-manifest — フレームワーク配布ファイルのハッシュ台帳（compatibility-contract.md 準拠）"
  echo "# update-project.sh がカスタマイズ検出（3分類）に使用する。手動編集しない"
  echo "version: ${VERSION:-unknown}"
  find .claude -type f | LC_ALL=C sort | xargs -d '\n' sha256sum
} > "$OUT"

COUNT=$(grep -c '^[0-9a-f]\{64\}' "$OUT" || true)
echo "✅ $OUT を生成（version: ${VERSION:-unknown}, $COUNT ファイル）"
