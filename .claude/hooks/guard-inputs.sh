#!/usr/bin/env bash
# PreToolUse (Write|Edit): 読み取り専用領域・生成物への手書きを拒否する。
#   - docs/00-inputs/ はユーザー持ち込み資料（RFP 原本）。INDEX.md と README.md 以外は書き換え不可
#   - deliverables/ は Office 納品物（office-deliverables の build.sh が Markdown 正本から生成）
#   - docs/01-rfp/extracted/ は RFP 原本のテキスト化（build.sh extract が生成）
# 依存なし（sed のみ）。拒否は exit 2 ＋ stderr の理由。
input=$(cat)
path=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)
[ -z "$path" ] && exit 0
rel="${path#"${CLAUDE_PROJECT_DIR:-$PWD}"/}"

case "$rel" in
  docs/00-inputs/INDEX.md|docs/00-inputs/README.md) exit 0 ;;
  docs/00-inputs/*)
    echo "docs/00-inputs/ はユーザーの持ち込み資料（RFP 原本）で読み取り専用です（INDEX.md のみ更新可）。解釈や補足は docs/01-rfp/rfp-analysis.md と OQ に書いてください。" >&2
    exit 2 ;;
  deliverables/*)
    echo "deliverables/ は生成物です。内容は docs/03-requirements/ の Markdown、体裁は docs/04-deliverables/*.yaml を直し、bash .claude/skills/office-deliverables/scripts/build.sh all で再生成してください。" >&2
    exit 2 ;;
  docs/01-rfp/extracted/*)
    echo "docs/01-rfp/extracted/ は RFP 原本の機械抽出です。bash .claude/skills/office-deliverables/scripts/build.sh extract で再生成してください。" >&2
    exit 2 ;;
esac
exit 0
