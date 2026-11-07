#!/usr/bin/env bash
# PostToolUse (Write): reviews/*-loopN.md に機械可読 Verdict ブロックが揃っているか検査する。
# 欠けていれば decision: block で理由を返し、書き直しを促す（PM がこのブロックを読んでループを回す）。
input=$(cat)
path=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n1)
case "$path" in
  */reviews/*-loop[0-9]*.md) ;;
  *) exit 0 ;;
esac
case "$path" in *-response-loop*) exit 0 ;; esac   # producer の対応表は対象外
[ -f "$path" ] || exit 0

missing=""
for key in "VERDICT:" "LOOP:" "RETURN_TO:" "REPORT:"; do
  grep -q "^${key}" "$path" || missing="$missing $key"
done
if grep -q "^VERDICT:" "$path" && ! grep -Eq "^VERDICT:[[:space:]]*(BLOCK|WARNING|APPROVE)\b" "$path"; then
  missing="$missing VERDICT=BLOCK|WARNING|APPROVE"
fi
[ -z "$missing" ] && exit 0

reason="レビューレポート ${path} に Verdict ブロックが不完全です（欠落:${missing}）。末尾に VERDICT: / LOOP: N/5 / RETURN_TO: / REPORT: の 4 行を追記してください（sdlc-toolkit SKILL.md §5）。"
printf '{"decision":"block","reason":"%s"}\n' "$(printf '%s' "$reason" | sed 's/"/\\"/g')"
exit 0
