# Changelog

このリポジトリのすべての注目すべき変更を記録する。

形式は [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) に準拠し、
バージョニングは [Semantic Versioning](https://semver.org/spec/v2.0.0.html) に従う。

## [Unreleased]

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
