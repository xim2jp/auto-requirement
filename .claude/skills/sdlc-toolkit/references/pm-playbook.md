# PM プレイブック（フェーズ表・status.md・文書セット・納品判定）

project-manager（通常はメインセッション自身）がフェーズを進めるための正本。共通契約は `SKILL.md`、修正ループは `rework-loop.md`。

## 1. フェーズ表

| Phase | 名称 | producer | reviewer / ゲート | 主な成果物 | 備考 |
|------:|------|----------|-------------------|-----------|------|
| 0 | RFP 配置 | （ユーザー） | PM が存在確認 | `docs/00-inputs/`（RFP 原本・参考資料） | **RFP は必須**。無ければ「RFP を置いてください」と案内し、雛形 `requirements-toolkit/templates/rfp.md` を示す。口頭の依頼しか無い場合は、ユーザーと一緒に雛形で RFP を書き起こして 00-inputs に置いてもらう |
| 1 | RFP 分析 | requirements-architect（RFP 分析モード） | **ユーザー確認**（§4） | `docs/01-rfp/rfp-analysis.md`、`docs/01-rfp/extracted/`、`docs/00-inputs/INDEX.md`、`docs/03-requirements/open-questions.md`（初版） | 起動前に PM が `build.sh extract` で Office 原本をテキスト化する |
| 2 | 要件定義 | requirements-architect | — | `docs/03-requirements/{requirements,business-requirements,use-cases,non-functional,permissions-matrix,glossary,open-questions,decision-log}.md`（モード A は proposal.md 任意） | ヒアリングは PM 経由でユーザーと対話。rfp-analysis.md の「対応 ID」を埋め戻す |
| 3 | 要件レビュー | — | requirements-reviewer | `docs/03-requirements/reviews/` | Approve 後、Handoff の完了判断材料（未決・要求量・投資と効果）を status.md に転記 |
| 4 | Office 成果物作成 | office-document-producer | — | `docs/04-deliverables/{deliverable-profile,summary-deck}.yaml`、`deliverables/*.{docx,xlsx,pptx}`、`check-report.md` | profile の文書情報（案件名・発注者・作成者・文書番号・版数・機密区分）はユーザーに確認済みであること |
| 5 | 成果物レビュー | — | deliverable-reviewer | `docs/04-deliverables/reviews/` | 差し戻し先は指摘ごと：体裁・構成 → office-document-producer、内容の誤り → requirements-architect（修正後に Phase 4 を再実行） |
| — | 納品判定 | PM | §5 | status.md に納品記録 | ユーザーへ納品物のパスと要点を報告 |

並列にできるものは無い（各フェーズが前フェーズの成果物を入力にする）。ただし Phase 2 の対話中に、確定した文書から順に Phase 4 の試し生成を行って体裁を早めに確かめるのはよい。

## 2. status.md

`docs/99-pm/status.md` がプロジェクトの単一の真実。初回起動時に無ければ作る（`.framework-version` を記録）。

```markdown
# プロジェクト進捗
- プロジェクト名 / 発注者 / 開始日 / 最終更新 / 現在フェーズ: Phase X / 5 / 次のアクション / フレームワーク版 / 納品版数

## フェーズ別ステータス
| Phase | 名称 | ステータス | 担当 | 成果物 | Verdict | ループ | 完了日 |
（0〜5 を全行。ループ列は N/5）

## 納品履歴
| 版数 | 納品日 | 内容 | 発注者の反応 |

## 未決事項（OQ）の推移 / エスカレーション履歴 / リスク・課題 / 意思決定ログ / 還流ループ記録
```

凡例：⏳ 待機・🚧 進行中・🔄 レビュー中・🔁 再レビュー中・⛔ Block 中・✅ 完了・⚠️ エスカレーション・📦 納品済。

## 3. 文書セット（Phase 1 完了時）

`document-set.md`（このディレクトリ）のプロファイル（`standard` / `light` / `proposal`）から、RFP の規模と提出物要求に合うものを初期値にして、作成する文書と Office 納品物の一覧をユーザーに提示し承認を得る。結果を `docs/99-pm/document-set.md` に書く（除外には理由）。以後、producer には採用文書だけを依頼し、reviewer には除外文書の不存在を指摘させない。RFP が提出物（文書名・形式）を指定していれば、それを最優先で document-set に反映する。

## 4. Phase 1 完了時のユーザー確認

RFP 分析の Handoff を読み、次を 1 回のメッセージでまとめて確認する（ここで聞いておくと Phase 4 で止まらない）：

1. **案件概要の確認**：RFP から読み取った目的（OBJ）・範囲・期限の要約。誤読があれば止めてもらう
2. **RFP の重大な矛盾・欠落**：要件定義の前に発注者へ確認すべきもの（MUST に影響する OQ）
3. **文書セット**：§3 の一覧
4. **成果物の文書情報**：案件名・発注者名（表紙の宛名）・作成者名・文書番号の有無・機密区分・初回の版数（例：0.9 レビュー版）。テンプレートや配色の指定があるか
5. **ヒアリングの進め方**：回答者（ユーザー本人か、発注者の担当者に転送するか）と期限

## 5. 納品判定

Phase 5 の deliverable-reviewer が Approve したら PM が判定する。**ひとつでも欠ければ納品しない**。

- `docs/03-requirements/reviews/` の最新 Verdict が APPROVE（または Warning 受容の記録あり）
- `docs/04-deliverables/check-report.md` が FAIL 0、WARN 全件に判断の記録がある
- 3 ファイルの版数・発行日・件数が一致し、改訂履歴に今回の版がある
- MUST に影響する open OQ には、発注者との先送り合意か、納品物上で「未決」と明示した記載がある

納品時はユーザーに、納品物 3 ファイルのパス、版数、要件の件数（BZ・UC・NFR）、未決事項の件数と期限、発注者に判断を求める事項を報告する。status.md の納品履歴に記録する。

## 6. 納品後の指摘・変更要求

発注者のレビュー指摘や変更要求は requirements-architect の変更要求手続き（`requirements-toolkit/references/requirements-management.md` §3）で受ける。PM は影響範囲を見て Phase 2 から再開し、Phase 3〜5 を通して版数を上げて再納品する（profile の `version` と `revisions` を更新）。RFP 自体の改訂版を受領したら 00-inputs に置いてもらい、Phase 1 の RFP 分析を差分更新してから進める。

## 7. PM が判断する場面

- Phase 1 完了時のユーザー確認（§4）
- Phase 3 Approve 後の進め方（未決が多い・要求量がベースラインを超えるなら、縮小・棚上げも提案）
- Warning の受容、ループ上限（5 回）到達、RFP と要望の矛盾、納品判定。**ここだけユーザーに聞く**。それ以外は進める
- フェーズ完了時に PROJECT_LEARNINGS.md への記録を一行で促す
