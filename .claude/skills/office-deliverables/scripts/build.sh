#!/usr/bin/env bash
# build.sh — Office 成果物の生成・検査のラッパー。プロジェクトルートの .venv を使い、無ければ作る。
# 使い方（プロジェクトルートで）:
#   bash .claude/skills/office-deliverables/scripts/build.sh extract            # RFP 原本（docx/xlsx/pptx）をテキスト化
#   bash .claude/skills/office-deliverables/scripts/build.sh [all|docx|xlsx|pptx|check] [--pdf] [--mermaid auto|npx|source|off]
set -e
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${CLAUDE_PROJECT_DIR:-$(pwd)}"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"

need_install=0
if [ ! -x "$PY" ]; then
  echo "🐍 $VENV を作成します"
  if command -v uv >/dev/null 2>&1; then uv venv -q "$VENV"; else python3 -m venv "$VENV"; fi
  need_install=1
fi
if [ "$need_install" = "1" ] || ! "$PY" -c "import docx, openpyxl, pptx, markdown_it, yaml" 2>/dev/null; then
  echo "📦 依存ライブラリを導入します（$HERE/requirements.txt）"
  if command -v uv >/dev/null 2>&1; then uv pip install -q --python "$PY" -r "$HERE/requirements.txt"; else "$PY" -m pip install -q -r "$HERE/requirements.txt"; fi
fi
cd "$ROOT"
if [ "$1" = "extract" ]; then
  shift
  exec "$PY" "$HERE/extract_inputs.py" . "$@"
fi
exec "$PY" "$HERE/office_build.py" "$@"
