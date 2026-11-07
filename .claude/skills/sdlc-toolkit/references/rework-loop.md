# Rework Loop（修正ループ）プロトコル

レビューで指摘が出たら、**前工程に自動で戻して修正 → 再レビュー**を Approve まで繰り返す。背景：レビュー報告で流れが止まり、指摘が放置されたまま次フェーズに進む事故が頻発した。レビュー報告はループ起動のトリガーであって終着点ではない。

## ループ

```
producer が成果物を提出（Self-Check + Handoff 付き）
  → reviewer が Verdict
     🟢 Approve → 次フェーズ
     🟡 Warning → ユーザーに「修正してループ」か「受容して進行（Defer 記録）」を確認
     🔴 Block   → PM が確認なしで producer を修正モードで起動
                  → producer が指摘対応＋対応表 → reviewer 再起動（ループ +1）→ Verdict へ
```

- ループカウント＝同一フェーズのレビュー実行回数（初回 1）。status.md の「ループ」列に `N/5`
- 上限 5 回。5 回目でも Approve（または Warning 受容）に至らなければ PM がエスカレーション
- ユーザーに聞くのは Warning 受容・上限到達・RFP の矛盾（発注者確認）の 3 場面だけ

## 三者の責務

**reviewer**：レポートを `reviews/YYYY-MM-DD-<reviewer>-loopN.md` に書き、末尾と完了報告に Verdict ブロック（`SKILL.md` §5）を置く。2 回目以降は対応表を照合し、対応表なし・無変更再提出は NO-CHANGE で Block。

**producer（修正モード）**：レビューレポートのパスを渡されたら、Critical / Major 全件に `修正済` / `代替案で対応` / `反論（根拠必須）` / `保留（ユーザー判断待ち）` のいずれかを付け、成果物を直し、対応表を `reviews/YYYY-MM-DD-<producer>-response-loopN.md` に書く。Minor / Nit は任意だが対応／見送りを記録する。

```markdown
# 指摘対応表（loop N）
- 対象レビュー: reviews/YYYY-MM-DD-<reviewer>-loopN.md  - 対応日: YYYY-MM-DD
| 指摘ID | 重要度 | 対応 | 反映箇所 | 備考 |
```

**project-manager**：Verdict ブロックを読み、BLOCK なら即座に `RETURN_TO` を修正モードで起動（レポートのパスを渡す）、producer 完了後に reviewer を再起動、status.md のループ列を更新。`LOOP: 5/5` で Block ならエスカレーション。

## エスカレーション（PM → ユーザー）

状況（未解決指摘の ID と要約）、ループ履歴（Loop / 日付 / Verdict / 残指摘の表）、選択肢（1. 発注者に確認して RFP・前提を確定する 2. Defer 記録付きで進行（納品物に未決として明示）3. スコープ・要件の見直し）、PM の推奨と理由、を示して判断を求める。

## 差し戻し先

| レビューフェーズ | reviewer | 差し戻し先（指摘ごとに該当者） |
|----------------|----------|------------------------------|
| 3 | requirements-reviewer | requirements-architect |
| 5 | deliverable-reviewer | office-document-producer（体裁・構成・スライド・プロファイル）／ requirements-architect（Markdown 正本の内容の誤り。修正後に office-document-producer が再生成） |

Phase 5 で内容の誤りが見つかったら、PM は requirements-architect を修正モードで起動し、変更が要件の判断に及ぶ（採否・優先度・NFR の値が変わる）なら Phase 3 の requirements-reviewer を新しいループで回してから Phase 4 に戻る。表記の修正だけなら Phase 4 の再生成に直行してよい。

**RFP に起因する問題**：RFP 自体の矛盾・欠落で要件が決まらないときは、本ループとは別に PM が発注者確認事項としてユーザーに提示する。RFP 原本を書き換えて吸収しない。回答が来たら OQ に転記し、requirements-architect が反映する。

## アンチパターン

レビュー報告で停止する／対応表なしの再提出／無変更再提出／ループ回数を記録しない／Warning を確認なしに受容する／上限を超えてループを続ける。
