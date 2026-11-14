# Changelog

このリポジトリのすべての注目すべき変更を記録する。

形式は [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) に準拠し、
バージョニングは [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に従う。

## [Unreleased]

### Changed
- ライト版スキル（`skillfile/rfp-requirements/SKILL.md`）の 2 ファイル（`rfp-analysis.md`・`requirements.md`）の形式を固定した。冒頭に文書情報（YAML front matter。`format: rfp-requirements-lite`・`format_version: 1`、案件名・発注者・作成者・版・作成日・文書番号・機密区分）を書き、章の見出しと番号、ID 台帳の列名、ID 体系をテンプレートどおりに保つ。フル版にアップロードして納品物に仕上げられるようにするため。セルフレビューに形式の検査（文書情報・見出し・未定義 ID・本文の作業痕跡）を追加し、RFP-NNN の行き先漏れ検査が §5 の表を誤検知しないようにした。OQ に「先送り基準」、UC に「業務領域」の列を足し、rfp-analysis.md §5 の前提に AS-NN を振る
- エージェントのモデルを役割で使い分けるようにした。本筋（rfp-writer・requirements-architect・project-manager）は opus、点検役（requirements-reviewer・deliverable-reviewer）は sonnet、生成スクリプトを動かす実作業（office-document-producer）は haiku。`check-harness.sh` は役割ごとの期待モデルで検査する（harness-authoring-guide.md §1-6）

## [2.0.1] - 2026-11-08

構想から納品までの通し運転（クリニックの予約・診療管理システム）で見つかった Office 納品物の不具合を直した。

### Fixed
- 要件定義要求書（RFP）：版数・発行日・問い合わせ窓口を `rfp.md` 冒頭の表から取り、改訂履歴・発行者・フッターを発注者名義にした（受注者側の版数・文書番号・改訂履歴が出ていた）。機密区分などは `rfp_word.project` で上書きできる。機械検査のファイル名照合も RFP の版数に合わせた
- Excel・PowerPoint にも正本のファイル名（`rfp.md` 等）を納品文書名に置き換える処理を適用。`docs/01-rfp/` などのパス付きの表記も置き換える
- Word：前付け（承認欄・改訂履歴・目次）の後の改ページを「段落前で改ページ」方式にし、目次がちょうど 1 ページのときの空白ページを解消。横向きページへの切り替えで、表の後の空段落がページ末からあふれて空白ページになる問題と、最初の横向きページが目次の直後から始まる問題を修正
- Word：見出し・表や図の導入文・表の見出し行と 1 行目を次と同じページに置き、見出しや見出し行だけがページ末に残る問題を修正
- Word：縦長の図の高さを本文の高さ − 3cm までに制限（図の名前だけのページを防ぐ）
- Word：目次スタイルを Word 組み込みの「toc N」にし行間を固定（独自スタイルが無視され目次が間延びしていた）。見出し 2 が 30 を超える文書は目次を見出し 1 までにする
- Word：横向きページでフッター右端の文字が中央寄りになる問題（既定テンプレートのタブ位置を消去）
- Word・Excel：表の見出しの英字語（MoSCoW など）や番号・2 文字の語（「10」「受付」）が途中で折り返す問題
- Excel：RFP 対応表を「トレーサビリティ(RFP)」シートに分け、要約列の出典と「その他の対応先」列を修正。BZ×UC マトリクスに「採否」「UC 対象外の理由」を追加し、UC が不要な BZ を対応漏れの候補に数えないようにした（機械検査の WARN 条件も同じ）。台帳シートの行の高さを内容から見積もり、PDF 化・印刷で文字が切れないようにした

## [2.0.0] - 2026-11-08

非エンジニアのユーザーを前提に、入口を「RFP の持ち込み（必須）」から「作りたいシステムの概要を話すだけ」に変えた。Phase 0 で RFP（要件定義要求書）を作り、Office 納品物に要件定義要求書と付録文書（別紙ごとの Word）を加えた。持ち込み RFP の流れはそのまま使える。

### Added
- **Phase 0 RFP 準備**：`rfp-writer` エージェント（質問作成 → 起草 → 修正）と `rfp-authoring` Skill（非エンジニア向けの聞き取り：最初に確かめる 7 点・質問バンク・規模別の推奨値・RFP 起草規則・セルフチェック、テンプレート `concept.md`・`rfp-document.md`）。成果物は `docs/01-rfp/concept.md`（ユーザーの原文と回答・仮定）と `docs/01-rfp/rfp.md`（RFP の正本）
- **Office 納品物**：要件定義要求書（RFP）の Word（発注者名義の表紙：宛名なし・発行＝発注者）。付録文書として別紙 1〜7 を単独の Word で出力（`word.appendix_mode: separate`。既定。`bundled` で従来どおり綴じ込み）。別紙の冒頭説明は表紙に置く
- `sdlc-toolkit` §9「ユーザーとの話し方（非エンジニア前提）」：質問は選択肢と「おまかせ（推奨）」付き、報告は専門用語・ID なし、用語の言い換え表
- 配布キットに利用者向けの `START_HERE.md`（`templates/kit/`）

### Changed
- SDLC：Phase 0 を「RFP 配置」から「RFP 準備（構想 → RFP 起草 → RFP の要点のユーザー確認）」に。Phase 1〜5 の番号と内容は維持（PM プレイブック・PM・requirements-architect・各レビュー役・テンプレートを更新）
- RFP 分析：構想から作った RFP の分析手順（`rfp-analysis.md` §9。「（想定）」と前提 AS-NN は OQ にしてヒアリングで確認、rfp.md の改訂は PM 経由で rfp-writer が版を上げる）
- requirements-architect のヒアリングと PM の中継：非エンジニア向けの言い換え・選択肢・推奨値を必須に
- 機械検査：生成した全 Word（要件定義要求書・要件定義書・別紙）を検査。`concept.md` は Office 化の対象外
- `setup.sh`・案件 `CLAUDE.md`・`docs/00-inputs/README.md`：「何も用意しなくてよい、話しかけるだけ」の案内に
- `smoke-test.sh`・`build-kit.sh --test`：要件定義要求書と別紙の生成を確認

## [1.1.0] - 2026-11-08

### Added
- 配布用 ZIP キット：`scripts/build-kit.sh` が README.md だけのリポジトリに解凍するだけで動くキット（`dist/rfp-requirements-kit-v<版>.zip`）を作り、`--test` で解凍 → Office 生成まで確認する。`v*` タグの push で GitHub Releases に自動添付（`.github/workflows/release.yml`）
- `setup.sh` に `SKIP_VENV=1`（Python 環境の作成を初回の build.sh に任せる）
- ライト版スキル `skillfile/rfp-requirements/SKILL.md`（1 ファイル）。他のリポジトリの `.claude/skills/` にコピーするだけで、RFP 分析表と要件定義書を Markdown で作成する。RFP 原本（docx / xlsx / pptx）のテキスト化は標準ライブラリだけのスクリプトを内蔵

## [1.0.0] - 2026-11-07

派生元の全工程 SDLC フレームワーク v0.18.0 を完全にコピーし、**RFP 起点の要件定義と Office 納品物の作成まで**に絞った派生フレームワークとして初版を切った。要件定義の方法論（IPA 準拠の BR → SR 2 層、記述規約、NFR 6 カテゴリ、OQ・変更要求の手続き）と `docs/03-requirements/` の成果物・ID 体系はフル版と互換。フル版の履歴（v0.1.0〜v0.18.0）はフル版リポジトリの CHANGELOG を参照。

### Added

- **SDLC（Phase 0〜5）**：RFP 配置（ユーザー・必須）→ RFP 分析 →〔ユーザー確認〕→ 要件定義 → 要件レビュー → Office 成果物作成 → 成果物レビュー → 納品判定。納品後の指摘・変更要求は Phase 2 から版数を上げて再納品
- **RFP 分析**（`docs/01-rfp/rfp-analysis.md`）：RFP を RFP-NNN に分解し、区分・出典・判定（明確／曖昧／矛盾／欠落／対象外）・要件定義での扱い・対応 ID を付ける。RFP の目的から達成目標 OBJ-NN を抽出。RFP 標準構成との突合で欠落を検出。`requirements-toolkit` に `references/rfp-analysis.md`・`templates/rfp-analysis.md`・`templates/inputs-index.md`
- **`office-deliverables` Skill**：Markdown 正本から Office 納品物を生成・検査するスクリプト群（Python：python-docx・openpyxl・python-pptx・markdown-it-py・PyYAML）
  - Word 要件定義書：表紙・承認欄・改訂履歴・目次フィールド・ヘッダー/フッター・別紙構成・表の体裁・横向きページ・Mermaid 画像化・社内節の除去・ファイル名の文書名置換
  - Excel 要件一覧：表紙・目次・集計（数式）・ID 台帳（列名の正規化と表種別ごとのシート分割、参照表の列統合）・トレーサビリティ・入力規則・条件付き書式・印刷設定
  - PowerPoint 要件定義サマリー：`summary-deck.yaml` のスライド構成から生成（title / agenda / section / bullets / kpi / table / two_column / before_after / steps / closing）。表の正本引用（`from`）と自動分割、文字量に応じた縮小
  - 機械検査（`check-report.md`）、RFP 原本（docx / xlsx / pptx）のテキスト化（`build.sh extract`）
  - `references/office-style-guide.md`（日本の業務文書の体裁基準・納品前チェックリスト・PDF 化と目視確認の手順）、`references/deck-spec.md`、`templates/deliverable-profile.yaml`・`templates/summary-deck.yaml`
- エージェント `office-document-producer`（Phase 4）・`deliverable-reviewer`（Phase 5）
- `sdlc-toolkit/references/document-set.md`（standard / light / proposal と Office 納品物の対応）
- `scripts/smoke-test.sh` と CI ジョブ `smoke`（new-project → setup → Office 生成の通し確認）
- `setup.sh` が `.venv` を作り Office 生成の依存を導入。`docs/04-deliverables/deliverable-profile.yaml` の雛形を配置

### Changed

- `project-manager`・`requirements-architect`・`requirements-reviewer` を RFP 起点に書き直し（企画書・戦略書・上流突合表への依存を RFP・RFP 分析に置換。OQ 種別を RFP 矛盾／RFP 曖昧／RFP 欠落に。Handoff の「上流差し戻し候補」を「発注者確認事項（RFP 改訂候補）」に）
- `sdlc-toolkit`：SKILL.md・pm-playbook・artifact-layout・review-protocol・rework-loop を 6 フェーズ体系に再構成。執筆ルールに「納品物として読める」規律（1 文目の書き方・作業痕跡の禁止・ID 台帳の表形式）を追加
- `requirements-toolkit`：全 references・templates を RFP 起点に再配線（OBJ は RFP から抽出、SEG を廃し SH / ROLE で表現、後工程は範囲外として一般化）
- hooks：`guard-inputs.sh` の保護対象を `docs/00-inputs/`・`deliverables/`・`docs/01-rfp/extracted/` に
- `check-harness.sh`：office-deliverables スクリプトの存在・構文を検査
- plugin 名を `rfp-requirements-framework` に

### Removed

- 要件定義に不要な 43 エージェント（企画・戦略・設計・実装・テスト・運用・マーケティング・各 specialist）と 26 Skill
- `sdlc-toolkit` の lifecycle-loop・test-hardening・tech-stack-profile・document-catalog・build-htmldocs.mjs（HTML 公開層は Office 納品物に置き換え）
- 生成案件向けの PR 二重レビューゲート（Amazon Q）・`setup-branch-protection.sh`・`loop-metrics.sh`
