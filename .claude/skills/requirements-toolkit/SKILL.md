---
name: requirements-toolkit
description: 発注者の RFP を起点に、漏れのない要件定義書へ変換するための知識集。IPA『ユーザのための要件定義ガイド 第2版』に基づき、RFP 分析（RFP-NNN 分解・欠落チェック・OBJ 抽出）、ビジネス要求→システム化要求（UC・非機能・権限）の 2 層プロセス、優先順位と採否、記述規約、ステークホルダ分析、要求量の制御、決まらない要件と完了判断、文書間整合チェックと、RFP 分析表・要件定義書・BZ・UC・NFR・ROLE・用語集・OQ・決定ログ・提案書のテンプレートを収録する。「RFP 分析」「要件定義」「要件レビュー」「ヒアリング」「業務要件」「ユースケース」「非機能要件」「提案書」で参照。
---

# Requirements Toolkit Skill

発注者の RFP を、開発着手・投資判断に耐える**要件定義書に変換する**ための知識集。対話の質（RFP 分析・プロセス・質問バンク・アンチパターン）と成果物の質（記述規約・文書ガイド・テンプレート・完全性チェック）の両面を支える。

> 基盤：IPA『ユーザのための要件定義ガイド 第2版 — 要件定義を成功に導く 128 の勘どころ』（2019）。IPA の「企画工程」は発注者側で行われ、その結論が RFP（Phase 0）である。本ハーネスは RFP 分析（Phase 1）でそれを確認し、「要件定義工程」を Phase 2（要件定義）・Phase 3（要件レビュー）として行う。「基本設計（外部設計）」以降は後工程（本ハーネスの範囲外）である。

## 本ハーネスのフェーズ

| Phase | 内容 | 担当 | 主な成果物 |
|-------|------|------|-----------|
| 0 | RFP 配置 | ユーザー | `docs/00-inputs/`（原本）、`docs/01-rfp/extracted/`（抽出テキスト） |
| 1 | RFP 分析 | requirements-architect → PM 確認 | `docs/01-rfp/rfp-analysis.md`、`docs/00-inputs/INDEX.md`、初版 `open-questions.md`、`docs/99-pm/document-set.md` |
| 2 | 要件定義 | requirements-architect | `docs/03-requirements/` 一式（モード A は任意で proposal.md） |
| 3 | 要件レビュー | requirements-reviewer | `docs/03-requirements/reviews/`（差し戻しは最大 5 ループ） |
| 4 | Office 成果物作成 | office-document-producer | `deliverables/*.docx｜xlsx｜pptx` |
| 5 | 成果物レビュー | deliverable-reviewer → PM 納品判定 | レビュー記録 |

## 使う場面

- RFP を読む：全入力の読込 → RFP-NNN 分解 → 区分・判定 → 標準構成との突合 → OBJ 抽出 → OQ 起票 → ヒアリング計画
- 要件を作る：RFP 分析表を入口に、現状・問題・課題 → 業務目的・手段 → 具体化 → 優先順位・採否 → UC・NFR・権限 → 推敲 → 完全性確認 → 対応 ID の後埋め → Handoff
- 要件を判定する：記述規約・文書ガイド・完全性チェックリスト・RFP 分析の確認項目をレビューの判定基準にする
- 着手を判断する：決まらない要件・中止選択肢・投資材料、要求量と変更要求の扱いを決める
- Office 化で読む：ID の意味と台帳の列構成を確かめる

## references / templates 一覧

| ファイル | 内容 | 使いどころ |
|---------|------|-----------|
| `references/rfp-analysis.md` | **RFP 分析の手順**。入力の読込（原本・抽出テキスト・PDF）、RFP-NNN への原子分解と出典、区分 9 種・判定 5 種、標準構成との突合（欠落チェック）、OBJ 抽出、資料間の優先順位、要件定義への写像と対応 ID の後埋め、ヒアリング計画、Phase 3 の確認項目、アンチパターン | Phase 1 の正本。Phase 2 の入口、Phase 3 の判定基準 |
| `references/requirements-process.md` | **BR → SR の 2 層プロセス**。5 語（問題・課題・目的・目標・手段）の定義、現状把握、ステークホルダ 3 層、なぜなぜ、業務目的と測定尺度（KGI/KPI・MEDIC）、業務手段と IT 手段、要求構造の妥当性・十分性、MECE・概念データモデル・状態遷移・業務パターン表、優先順位 6 基準・MoSCoW・採否、棄却と先送り、合意形成、成果物の作成順 | Phase 2 の進行の正本 |
| `references/requirements-management.md` | **マネジメント**。ステークホルダの特定（7 種の要件と聞き先）、要求量の制御（発散／収束・ベースライン・機能化しない基準）、変更手続き、トレーサビリティ台帳、形式品質 3 チェック、決まらない要件（3 択・先送り基準）、完了判断（完了基準・材料・中止選択肢）、投資効果の概算 | 要求が膨らんだとき、未決が残るとき、Phase 3 へ渡す前 |
| `references/writing-rules.md` | **要件記述規約**。一文一義・単文・である調・数式化・形容詞副詞の数値補足、助詞の規約、口頭言語禁止、禁止語（Block／Major）、MEDIC、用語統一、ビジネスルールの記法選択表、推敲手順 | 全文書のドラフト前と reviewer の Grep |
| `references/document-guide.md` | **文書ガイド**。本ハーネスの文書と IPA 文書の対応、全件／主要、完成の定義（誰と合意）、後工程で作る文書と Phase 2 で確定する部分、粒度レベル 1〜4、文書間整合チェック、台帳の書式（Office 化の前提）、文書構成の宣言 | 作成前の計画と reviewer の第 1 パス |
| `references/non-functional-requirements.md` | 非機能要件 6 カテゴリ（AVL/PERF/OPS/MIG/SEC/ENV）の決め方と既定値の一例（Tier A）。RFP の条件が優先。ビジネス領域の要求 → メトリクス、条件付き値、検証方法、運用・移行の取り込み | NFR の対話と non-functional.md 記載 |
| `references/question-bank-client.md` | モード A（クライアント案件）向け質問バンク（プロセス順。RFP で答えが出ている問いは転記と明示） | モード A の対話 |
| `references/question-bank-product.md` | モード B（自社プロダクト）向け質問バンク（同上） | モード B の対話 |
| `references/anti-patterns.md` | 「気持ちよく進んでいるのに浅い」要件定義を防ぐセルフチェック（24 兆候。IPA の 27 問題から転用した 13〜23、RFP の扱い 24 を含む） | 対話の全ターン |
| `references/completeness-checklist.md` | ドラフト前・Phase 3 引き渡し前の完全性確認（RFP／ステークホルダ／現状／目的・手段／具体化／SR／NFR／制約／スコープ／受入／マネジメント／記述品質） | ドラフト作成の直前 |
| `templates/rfp-analysis.md` | RFP 分析表（RFP-NNN）。RFP 概要・モード、達成目標 OBJ、要求分解表（区分・出典・判定・扱い・対応 ID・OQ）、標準構成との突合、曖昧・矛盾・欠落、前提、ヒアリング計画 | Phase 1 |
| `templates/inputs-index.md` | 持ち込み資料一覧（docs/00-inputs/INDEX.md）。種別・版・受領日・抽出テキストのパス・上書き記録 | Phase 1（随時更新） |
| `templates/requirements-doc.md` | 要件定義書（正本）テンプレ。文書構成の宣言、RFP からの確定事項、ステークホルダ、現状、スコープ（業務プロセス関連図）、業務モデル（概念データモデル・状態遷移）、外部 I/F、受入テスト観点、投資と効果、Before/After | 成果物作成 |
| `templates/business-requirements.md` | 業務要件一覧（BZ-NNN）。問題・課題一覧、要求構造、目的系／手段系要求、6 基準・MoSCoW・採否、業務パターン表、問題⇄要求照合、変更履歴 | 成果物作成 |
| `templates/use-cases.md` | ユースケース一覧（UC-<KEY>-NN）。一覧＋記述（事前/事後条件・基本/代替/例外・CRUD・業務ルール表・理由）、例外・特殊処理の抽出チェック、標準 UC カタログ差分 | 成果物作成 |
| `templates/non-functional.md` | 非機能要件一覧（NFR-<CAT>-NN）。§0 ビジネス領域の要求、6 カテゴリ × 条件 × 差分理由 × 優先度 × 検証方法、トレードオフ | 成果物作成 |
| `templates/permissions-matrix.md` | ロール・権限マトリクス初版（ROLE-NN）。ロール × UC、ロール × エンティティ × CRUD、エンティティ × UC の CRUD 俯瞰（抜け漏れ検証） | 成果物作成 |
| `templates/glossary.md` | 用語集。管理対象の MECE 分類、業務用語定義（同義語＝禁止語・略語・利用可否）、禁止語一覧 | 成果物作成（成長型） |
| `templates/open-questions.md` | 要確認事項一覧（OQ-NNN）。種別（RFP 矛盾・RFP 欠落・RFP 曖昧・未決要件・調査・変更要求）、影響評価、仮決め、先送り基準、決まらない要件の 5 条件 | Phase 1 で初版、以降随時 |
| `templates/decision-log.md` | 判断・確認の記録（D-NNN）。台帳と詳細記録。要求の採否・変更要求・未決の取り扱いを含む | 対話と並行して随時 |
| `templates/rfp.md` | RFP の標準構成。RFP 分析の欠落チェックと、ユーザーが RFP を書くときの雛形 | Phase 1 の突合、RFP 作成支援 |
| `templates/proposal.md` | 提案書ドラフトテンプレ（Before/After 1 枚サマリー付き） | モード A の任意成果物 |

## 重要原則

1. **要件定義の上流は RFP である**。経営レベルの目的（OBJ）・制約・提出物は RFP 分析（Phase 1）で RFP 原文から出典付きで抽出済み。Phase 2 は**確認して転記**し、聞き直さない。食い違い・曖昧・欠落は OQ にして発注者に確認する
2. **RFP を黙って上書きしない・黙って捨てない**。ステークホルダの要望が RFP と矛盾したら OQ（RFP 矛盾）にする。対象外にした RFP 項目は理由付きで残す。全 RFP-NNN に対応 ID か対象外の理由を持たせる
3. **RFP の全要求を MUST にしない**。RFP は要求であって要件ではない。優先順位と採否は要件定義で決め、発注者の合意を取る
4. **問題・課題・目的・目標・手段の 5 語を厳密に使い分ける**。要求には「〜を達成したい（目的）」と「〜を実施したい（手段）」の 2 種類があり、業務目的（BZ）を抜いた「中抜け」を禁止する
5. **「現行踏襲」を要求として受け入れない**。現行を書き下ろし、To-Be でも必要な根拠を付ける
6. **目標は測れる形で**。測定尺度・現状値・目標値・達成時期。述語は MEDIC（維持・廃止・削減・増加・創出）。「強化」「改善」禁止
7. **業務手段を IT 手段と同じ重みで検討する**。作らない選択肢（運用・サポート・既存 SaaS）を必ず候補に入れる。難しい判断ロジックは人に残す方が安く柔軟
8. **要求は捨てる・先送りする**。6 基準で粗く判定し、採否列を優先度と別に持つ。棄却・先送りは理由付きで残す。60 点で出して育てる
9. **業務ルールは自然言語の長文で書かない**。表・式・デシジョンテーブル・状態遷移図・CRUD 表に落とす。記述規約（writing-rules.md）に従い、禁止語は Grep で 0 件にする
10. **質問バンクは全部聞かない**。RFP で答えが出ている問いは聞かない。1 ターン 3 問以内、5 問ごとに復唱
11. **判断は decision-log に即記録**。要求の採否・変更要求・未決の取り扱い・RFP 解釈も含めて「なぜこの仕様になったか」を追跡可能にする
12. **決まらない要件を放置しない**。OQ に全件列挙し、影響評価と先送り基準を満たすものだけ持ち越す。完了判断では中止・棚上げも選択肢に入れ、投資額・回収額の甘い自己査定を疑う
13. **文書間は ID で結び、機械的に整合を確認する**。RFP → OBJ → BZ → UC/NFR/ROLE（→ 後工程の機能・画面・API・テスト）。従属値一致・重複・参照元存在の 3 チェック。システム化しない要求も台帳に残す
14. **台帳は Office 化できる形で書く**。ID 台帳は 1 列目が `ID` の Markdown 表、同種の表は列名を揃える。冒頭「この文書について」の第 1 文は発注者が読める文にする。`✅ Self-Check`・`📤 Handoff` は文書末尾に置く（納品物からは自動で除かれる）
15. **成果物は `docs/01-rfp/`・`docs/03-requirements/` に配置**（sdlc-toolkit の artifact-layout.md に従う）。作る文書は document-set.md で確定したものだけ。無い文書には理由を書く

## 成果物の作成順

```
Phase 1（RFP 分析）
0. INDEX.md 更新 → rfp-analysis.md（§1 概要・モード → §3 分解 → §4 欠落チェック → §2 OBJ → §5 OQ → §7 ヒアリング計画）
   ＋ open-questions.md 初版  → PM がユーザーと確認（案件概要・document-set.md・優先質問）
Phase 2（要件定義）
1. requirements.md §0〜§4（文書構成・概要・RFP からの確定事項・ステークホルダ・現状）
2. business-requirements.md §1〜§3（問題・課題 → 要求構造 → BZ 目的・手段）
3. glossary.md（管理対象の MECE・禁止語）／requirements.md §7（概念データモデル・状態遷移）
4. business-requirements.md §3.2 採否・§4 業務パターン → requirements.md §6 スコープ（MVP・先送り・やらないこと）
5. use-cases.md／permissions-matrix.md／non-functional.md（SR）／requirements.md §9 外部 I/F・§13 運用・移行・§14 受入
6. open-questions.md／decision-log.md（随時）
7. rfp-analysis.md §3 の対応 ID を後埋め（全 RFP-NNN に行き先か対象外の理由）
8. writing-rules §7 推敲 → completeness-checklist → Self-Check → Handoff（発注者確認事項・決まらない要件・中止検討・投資材料）
9. （モード A・任意）proposal.md
```
