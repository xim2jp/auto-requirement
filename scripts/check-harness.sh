#!/bin/bash
# check-harness.sh - エージェント / Skill 定義がハーネス執筆ガイド（docs/operations/harness-authoring-guide.md）に沿っているかを検査する。
# CI（framework-checks.yml）から実行。失敗は exit 1。警告は exit 0。
# 使い方: bash scripts/check-harness.sh [--strict]（--strict で警告も失敗扱い）

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
AGENTS="$ROOT/.claude/agents"
SKILLS="$ROOT/.claude/skills"
STRICT=0; [ "$1" = "--strict" ] && STRICT=1
ERR=0; WARN=0
err()  { echo "❌ $1"; ERR=$((ERR+1)); }
warn() { echo "⚠️  $1"; WARN=$((WARN+1)); }

frontmatter() { awk 'NR==1{if($0!="---"){exit 1}; next} /^---$/{exit} {print}' "$1"; }
field() { frontmatter "$1" | sed -n "s/^$2:[[:space:]]*//p" | head -n1; }

echo "🔍 ハーネス検査"
echo ""
echo "── agents"
for f in "$AGENTS"/*.md; do
  base=$(basename "$f" .md)
  if ! frontmatter "$f" >/dev/null 2>&1 || [ -z "$(frontmatter "$f")" ]; then err "$base: frontmatter が無い（1 行目が --- ではない）"; continue; fi
  name=$(field "$f" name); desc=$(field "$f" description); model=$(field "$f" model)
  [ "$name" = "$base" ] || err "$base: name:$name がファイル名と一致しない"
  [ -n "$desc" ] || err "$base: description が無い"
  dlen=$(printf '%s' "$desc" | wc -m)
  [ "$dlen" -le 400 ] || warn "$base: description が ${dlen} 字（目安 300、上限 400）"
  [ "$model" = "inherit" ] || warn "$base: model が inherit ではない（$model）"
  frontmatter "$f" | grep -qE '^\s*-\s*sdlc-toolkit\s*$' || err "$base: skills に sdlc-toolkit が無い"
  if grep -qE 'v0\.[0-9]+(\.[0-9]+)?' "$f"; then warn "$base: 版数注記 $(grep -oE 'v0\.[0-9]+(\.[0-9]+)?' "$f" | sort -u | tr '\n' ' ')が残っている"; fi
  size=$(wc -c < "$f")
  [ "$size" -le 10240 ] || warn "$base: ${size} bytes（目安 8KB、上限 10KB）"
  # skills に書いた Skill が存在するか
  for s in $(frontmatter "$f" | awk '/^skills:/{f=1;next} f&&/^\s*-/{sub(/^\s*-\s*/,"");print;next} f&&!/^\s/{f=0}'); do
    [ -d "$SKILLS/$s" ] || err "$base: skills に存在しない Skill '$s'"
  done
done

echo "── skills"
for f in "$SKILLS"/*/SKILL.md; do
  dir=$(basename "$(dirname "$f")")
  if ! frontmatter "$f" >/dev/null 2>&1 || [ -z "$(frontmatter "$f")" ]; then err "$dir: frontmatter が無い"; continue; fi
  name=$(field "$f" name); desc=$(field "$f" description)
  [ "$name" = "$dir" ] || err "$dir: name:$name がディレクトリ名と一致しない"
  dlen=$(printf '%s' "$desc" | wc -m)
  [ "$dlen" -le 500 ] || warn "$dir: description が ${dlen} 字（上限 400 目安）"
  lines=$(wc -l < "$f")
  [ "$lines" -le 500 ] || warn "$dir: SKILL.md が ${lines} 行（上限 500）"
  grep -qE 'v0\.[0-9]+(\.[0-9]+)?' "$f" && warn "$dir: SKILL.md に版数注記が残っている"
done

echo "── 差し戻し先・連携先の実在（rework-loop.md / pm-playbook.md）"
for ref in "$SKILLS/sdlc-toolkit/references/rework-loop.md" "$SKILLS/sdlc-toolkit/references/pm-playbook.md"; do
  for a in $(grep -oE '[a-z0-9]+(-[a-z0-9]+)+' "$ref" | sort -u); do
    case "$a" in *-*-*|*-*) ;; *) continue;; esac
    # エージェント名らしい語（既知のサフィックス）だけ検査
    echo "$a" | grep -qE '(-planner|-reviewer|-strategist|-architect|-designer|-builder|-director|-specialist|-worker|-tester|-auditor|-analyst|-facilitator|-generator|-producer|-guardian|-adversary|-manager)$' || continue
    [ -f "$AGENTS/$a.md" ] || err "$(basename "$ref"): 存在しないエージェント '$a' を参照"
  done
done

echo "── plugin.json の agents 一覧"
PJ="$ROOT/.claude-plugin/plugin.json"
if [ -f "$PJ" ]; then
  for f in "$AGENTS"/*.md; do
    grep -q "\"./.claude/agents/$(basename "$f")\"" "$PJ" || err "plugin.json の agents に $(basename "$f") が無い"
  done
  for a in $(grep -oE '\./\.claude/agents/[^"]+\.md' "$PJ"); do
    [ -f "$ROOT/$a" ] || err "plugin.json の agents にある $a が存在しない"
  done
fi

echo "── office-deliverables スクリプト"
OD="$SKILLS/office-deliverables/scripts"
for f in build.sh office_build.py extract_inputs.py docx_builder.py xlsx_builder.py pptx_builder.py check.py mdparse.py profile.py common.py requirements.txt; do
  [ -f "$OD/$f" ] || err "office-deliverables/scripts/$f が無い"
done
[ -x "$OD/build.sh" ] || err "office-deliverables/scripts/build.sh に実行権限が無い"
command -v python3 >/dev/null && for f in "$OD"/*.py; do python3 -m py_compile "$f" 2>/dev/null || err "$(basename "$f") に構文エラー"; done

echo "── hooks"
[ -f "$ROOT/.claude/settings.json" ] || err ".claude/settings.json が無い"
for h in guard-inputs.sh check-review-report.sh; do
  [ -x "$ROOT/.claude/hooks/$h" ] || err ".claude/hooks/$h が無いか実行権限が無い"
done
command -v jq >/dev/null && { jq empty "$ROOT/.claude/settings.json" 2>/dev/null || err "settings.json が不正な JSON"; }

echo ""
echo "結果: エラー $ERR 件 / 警告 $WARN 件"
[ "$ERR" -gt 0 ] && exit 1
[ "$STRICT" = "1" ] && [ "$WARN" -gt 0 ] && exit 1
exit 0
