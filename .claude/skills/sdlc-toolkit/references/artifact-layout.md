# 成果物配置（Artifact Layout）

成果物のパスと命名の正本。パスは安定 API であり、エージェント定義・スクリプト・hook がこのパスを前提にする（`scripts/check-layout-drift.sh` が整合を検査する）。

## 1. ディレクトリ構造

```
<project-root>/
├── CLAUDE.md                      # PM としてのメインコンテキスト
├── PROJECT_LEARNINGS.md           # 案件の気付き（還流の一次資料）
├── .framework-version
├── docs/
│   ├── 00-inputs/                 # ユーザーの持ち込み資料（任意。RFP・構想メモ・参考資料。読み取り専用。INDEX.md・README.md のみエージェントが更新）
│   │   ├── INDEX.md               # 資料一覧（種別・版・受領日・抽出テキスト）
│   │   ├── rfp.*                  # 持ち込み RFP の原本（あれば。.md / .docx / .xlsx / .pptx / .pdf。複数可）
│   │   └── materials/             # 参考資料（現行資料・議事録・業務フロー・帳票サンプル）
│   ├── 01-rfp/                    # Phase 0：RFP 準備／Phase 1：RFP 分析
│   │   ├── concept.md             # 構想の聞き取り記録（ユーザーの原文・質問と回答・仮定）。社内用で Office 化しない
│   │   ├── rfp.md                 # 構想から作成した RFP の正本（要件定義要求書）。ユーザー確認済みの版
│   │   ├── rfp-analysis.md        # RFP 要求分解表（RFP-NNN）・達成目標（OBJ-NN）・欠落チェック・ヒアリング計画
│   │   ├── extracted/             # Office 原本のテキスト化（extract_inputs.py が生成。手で直さない）
│   │   └── reviews/
│   ├── 03-requirements/           # Phase 2-3：要件定義の正本（後工程・派生元の全工程 SDLC フレームワーク Phase 5 と互換）
│   │   ├── requirements.md        # 要件定義書（本編）
│   │   ├── business-requirements.md  # 業務要件（BZ-NNN）
│   │   ├── use-cases.md           # ユースケース（UC-<KEY>-NN）
│   │   ├── non-functional.md      # 非機能要件（NFR-<CAT>-NN）
│   │   ├── permissions-matrix.md  # ロール・権限（ROLE-NN）
│   │   ├── glossary.md            # 用語集
│   │   ├── open-questions.md      # 要確認事項（OQ-NNN）
│   │   ├── decision-log.md        # 決定ログ（D-NNN）
│   │   ├── proposal.md            # 提案書（モード A・任意）
│   │   └── reviews/               # requirements-reviewer のレポートと対応表
│   ├── 04-deliverables/           # Phase 4-5：Office 納品物の入力と検査
│   │   ├── deliverable-profile.yaml  # 文書情報・体裁・別紙／シート構成
│   │   ├── summary-deck.yaml      # 要件定義サマリーのスライド構成
│   │   ├── check-report.md        # 機械検査レポート（スクリプト生成）
│   │   ├── build-stats.json       # 生成統計（スクリプト生成）
│   │   └── reviews/               # deliverable-reviewer のレポートと対応表
│   └── 99-pm/
│       ├── status.md              # 進捗の単一の真実
│       └── document-set.md        # 作成する文書と Office 納品物の確定記録
├── deliverables/                  # Office 納品物（生成物。手書き不可）
│   ├── 要件定義要求書_<案件名>_v<版>.docx   # 構想から RFP を作った案件のみ
│   ├── 要件定義書_<案件名>_v<版>.docx
│   ├── 別紙N_<タイトル>_<案件名>_v<版>.docx # 付録文書（appendix_mode: separate のとき）
│   ├── 要件一覧_<案件名>_v<版>.xlsx
│   └── 要件定義サマリー_<案件名>_v<版>.pptx
└── tmp/                           # 作業用（PDF 化・ページ画像・Mermaid キャッシュ）。納品物に混ぜない
```

## 2. 命名

- レビュー：`docs/<dir>/reviews/YYYY-MM-DD-<reviewer>-loopN.md`（N は同一フェーズのレビュー回数。上書きしない）
- 指摘対応表：`docs/<dir>/reviews/YYYY-MM-DD-<producer>-response-loopN.md`
- Office 納品物：profile の `output.filename_pattern`（既定 `{kind}_{project}_v{version}`）。版を上げると新しいファイルになり、旧版は残る

## 3. ID 体系

| ID | 対象 | 定義する文書 | 例 |
|----|------|-------------|----|
| Q-NN | 構想の聞き取りの質問と回答 | concept.md §3 | Q-03 |
| REQ-NNN / P-NNN | 作成した RFP の要求・問題（RFP 分析で RFP-NNN に分解される） | rfp.md §4.2 / §2.2 | REQ-004 |
| RFP-NNN | RFP の要求項目（1 項目 1 要求） | rfp-analysis.md §3 | RFP-012 |
| OBJ-NN | 達成目標（RFP の目的から抽出） | rfp-analysis.md §2 | OBJ-01 |
| SH-NN | ステークホルダ | requirements.md §3 | SH-03 |
| BZ-NNN | 業務要件（目的系・手段系） | business-requirements.md | BZ-004 |
| PT-N | 業務パターン | business-requirements.md §4 | PT-2 |
| UC-<KEY>-NN | ユースケース | use-cases.md | UC-ORDER-03 |
| NFR-<CAT>-NN | 非機能要件（AVL / PERF / OPS / MIG / SEC / ENV） | non-functional.md | NFR-SEC-02 |
| ROLE-NN | ロール | permissions-matrix.md | ROLE-02 |
| IF-NN | 外部インターフェース | requirements.md §9 | IF-01 |
| TP-NN | 変革ポイント（As-Is → To-Be） | requirements.md §7.3 | TP-02 |
| RSK-NN | リスク | requirements.md §16 | RSK-03 |
| TERM-NNN | 用語 | glossary.md §2 | TERM-014 |
| AS-NN | 前提・仮定 | rfp.md §13（構想から作った案件）／rfp-analysis.md §6 | AS-03 |
| IN-NN | 持ち込み資料 | docs/00-inputs/INDEX.md | IN-01 |
| OQ-NNN | 要確認事項 | open-questions.md | OQ-007 |
| D-NNN | 決定 | decision-log.md | D-012 |

トレーサビリティ：RFP → OBJ → BZ → UC / NFR / ROLE（→ 後工程で F / S / API / テスト）。Excel 要件一覧のトレーサビリティシートは、この参照を台帳の記載から機械抽出する。

## 4. 後工程との互換

`docs/03-requirements/` のファイル名・ID 体系・節構成は フル版（派生元の全工程 SDLC フレームワーク）の Phase 5 成果物と同じである。後工程をフル版で行う場合は、このディレクトリをフル版の案件にコピーし、`docs/01-rfp/rfp-analysis.md` を `docs/00-inputs/` の参考資料として渡す。
