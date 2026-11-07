#!/bin/bash
# check-layout-drift.sh - エージェント/Skill 定義と artifact-layout.md の整合性検証（v0.12.0）
# エージェント・Skill が参照する docs/NN-xxx ディレクトリが artifact-layout.md に定義されているかを機械チェックする。
# compatibility-contract.md の「自己整合性の検証」の実装。CI（framework-checks.yml）から実行。
# 使い方: bash scripts/check-layout-drift.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LAYOUT="$ROOT/.claude/skills/sdlc-toolkit/references/artifact-layout.md"

if [ ! -f "$LAYOUT" ]; then
  echo "❌ artifact-layout.md が見つかりません: $LAYOUT"
  exit 1
fi

# artifact-layout.md に定義されているディレクトリ（docs/NN-xxx 形式）
DEFINED=$(grep -oE '[0-9]{2}(\.[0-9])?-[a-z-]+' "$LAYOUT" | sort -u)

# エージェント・Skill が参照しているディレクトリ
REFERENCED=$(grep -rhoE 'docs/[0-9]{2}(\.[0-9])?-[a-z-]+' "$ROOT/.claude/agents" "$ROOT/.claude/skills" 2>/dev/null \
  | sed 's|docs/||' | sort -u)

DRIFT=0
echo "🔍 レイアウトドリフト検査"
echo ""
for dir in $REFERENCED; do
  if ! echo "$DEFINED" | grep -qx "$dir"; then
    echo "❌ docs/$dir がエージェント/Skill から参照されていますが、artifact-layout.md に定義がありません:"
    grep -rlE "docs/$dir" "$ROOT/.claude/agents" "$ROOT/.claude/skills" | sed "s|$ROOT/|   - |" | head -5
    DRIFT=1
  fi
done

if [ "$DRIFT" = "0" ]; then
  echo "✅ ドリフトなし（参照ディレクトリ $(echo "$REFERENCED" | wc -l) 種はすべて artifact-layout.md に定義済み）"
else
  echo ""
  echo "対応: artifact-layout.md に追記するか、エージェント側の参照パスを修正してください"
  echo "（成果物パスは安定APIです。compatibility-contract.md 参照）"
  exit 1
fi
