# RFP Requirements Framework

**「作りたいシステムの概要」を話すだけで、RFP（要件定義要求書）を作り、要件定義を行い、Microsoft Office の納品物まで仕上げる** Claude Code 向けハーネス（6 エージェント + 4 Skill + hooks）。使う人は非エンジニアを想定している。RFP を持っていれば、それを起点にもできる。

> 派生元の全工程 SDLC フレームワーク（v0.18.0、46 エージェント + 28 Skill、企画→運用の円環 SDLC）から、**要件定義までの工程だけ**を切り出して簡略化し、Office 納品物の生成を加えたもの。要件定義の方法論（IPA『ユーザのための要件定義ガイド 第2版』準拠の BR → SR 2 層）はフル版と同じで、`docs/03-requirements/` の成果物はフル版の Phase 5 と互換。

## バージョン

現在: `2.0.0`（CHANGELOG.md）

## 何をするか

```
Phase 0  RFP 準備                      ユーザーが構想を話す → rfp-writer が質問（1 回 3 問・選択肢と「おまかせ」付き・最大 3 回）
                                        → docs/01-rfp/rfp.md（要件定義要求書）を起草 →〔ユーザー確認〕RFP の要点（専門用語なし）
                                        ※ RFP を持っていれば docs/00-inputs/ に置くだけ
Phase 1  RFP 分析                      requirements-architect → docs/01-rfp/rfp-analysis.md（RFP-NNN 分解・矛盾/曖昧/欠落・OQ）
         〔ユーザー確認〕案件概要・重大な矛盾・文書セット・納品物の文書情報・ヒアリングの進め方
Phase 2  要件定義（ヒアリング）         requirements-architect → docs/03-requirements/（BZ・UC・NFR・ROLE・用語・OQ・決定ログ）
Phase 3  要件レビュー                  requirements-reviewer ⇄ 修正ループ（上限 5 回）
Phase 4  Office 成果物作成             office-document-producer → deliverables/（Word：要件定義要求書・要件定義書・付録文書、Excel、PowerPoint）
Phase 5  成果物レビュー                deliverable-reviewer ⇄ 修正ループ → PM 納品判定 → 納品
         納品後の指摘・変更要求 → Phase 2 から版数を上げて再納品
```

ユーザーが話す相手は PM（メインセッション）だけ。PM が専門エージェントを起動し、レビューの Block は自動で修正ループに入る。ユーザーへの質問・報告は専門用語と ID を使わずに行い、「分からない」には推奨値で仮定して進める（仮定は成果物に明記し、あとで確認する）。

## ライト版（スキル 1 ファイルだけ）

エージェント・hooks・Office 生成なしで、**RFP 分析表と要件定義書を Markdown で作る**だけの単体スキルを `skillfile/` に置いている。既存のリポジトリにフォルダごとコピーすれば動く。

```bash
# 自分のリポジトリに入れる（ユーザー全体で使うなら ~/.claude/skills/ に置く）
mkdir -p .claude/skills
cp -r <このリポジトリ>/skillfile/rfp-requirements .claude/skills/

# RFP を置いて Claude Code に頼む
claude
> docs/rfp.pdf の RFP から要件定義書を作って
```

| | ライト版（`skillfile/rfp-requirements/`） | フルハーネス（本リポジトリの `.claude/`） |
|---|---|---|
| 構成 | `SKILL.md` 1 ファイル | 6 エージェント + 4 Skill + hooks + スクリプト |
| 入力 | RFP（必須） | 構想を話すだけ（RFP があればそれでも可） |
| 出力 | `docs/requirements/rfp-analysis.md`・`requirements.md`（Markdown） | `docs/` 一式 ＋ Word・Excel・PowerPoint |
| レビュー | セルフレビュー（Grep ＋ チェックリスト） | 独立したレビュー役が修正ループを回す（最大 5 回） |
| 前提 | Claude Code だけ（Office 原本の読込に python3） | bash・Python 3.10+ |

## Office 納品物

| 納品物 | 読み手 | 中身 |
|-------|-------|------|
| **要件定義要求書（RFP）**（.docx） | 発注者（名義人）・要件定義の担当 | 構想から作った RFP。表紙は発注者名義（宛名なし・発行＝発注者）。背景・目的・利用者・求める機能・品質条件・制約・未決事項・前提（想定）。持ち込み RFP の案件では作らない |
| **要件定義書**（.docx） | 発注者の担当・決裁者（合意・承認の正式文書） | 表紙・承認欄・改訂履歴・自動目次・ヘッダー/フッター（機密区分・文書番号・ページ x/y）、本編。表はヘッダー色・繰返し・縞・列幅自動、8 列以上の表は横向きページ。Mermaid 図は mmdc があれば画像化。社内向けの節（Self-Check・Handoff）とファイル名は自動で除去・置換（他文書への参照は「別紙1「業務要件一覧」」などに） |
| **付録文書**（別紙 1〜7 の .docx） | 詳細を確認する担当者 | 業務要件一覧・ユースケース一覧・非機能要件一覧・ロール・権限マトリクス・用語集・要確認事項一覧・RFP 要求分析表を 1 本ずつ。表紙（冒頭説明付き）・目次・本文。profile の `word.appendix_mode: bundled` で要件定義書に綴じ込みも可 |
| **要件一覧**（.xlsx） | 発注者・開発側の担当（管理台帳） | 表紙・目次（リンク）・集計（COUNTIF 数式で連動）・ID 台帳（OBJ・RFP・BZ・UC・NFR・ROLE・IF・SH・用語・OQ・D）・トレーサビリティ（BZ × UC、RFP → 対応 ID、漏れ候補を色付け）。見出し固定・フィルタ・入力規則（MoSCoW・採否・ステータス）・条件付き書式・A4 横印刷設定 |
| **要件定義サマリー**（.pptx、16:9） | 決裁者（承認会議で 15 分説明） | 表紙・目次・章扉・キーメッセージ付き本文（箇条書き／KPI／表／2 段比較／Before-After／ステップ）・今後の進め方。表は Markdown 正本から引用して 9 行ごとに自動分割、文字量に応じて自動縮小、話者ノートに出典 |

Markdown（`docs/`）が正本、Office は機械生成物（手で直さない。hook が `deliverables/` への書き込みを拒否）。生成後に機械検査（目次・ページ番号・台帳件数の一致・書きかけ表記・社内用語の混入・未定義 ID）を行い、さらに PDF 化したページ画像で目視確認する。

## クイックスタート

```bash
# 0. 取得
git clone https://github.com/xim2jp/auto-requirement.git ~/rfp-requirements-framework
cd ~/rfp-requirements-framework

# 1. 新規案件を作る（.claude/ 配置・docs/ 構造・status.md・Python 環境 .venv まで自動）
bash scripts/new-project.sh ~/projects/acme-order-system
cd ~/projects/acme-order-system

# 2. Claude Code を起動して、作りたいシステムのことを話しかける
claude
> 美容室の予約をスマホで受けられるようにしたい。今は電話と紙の台帳で、営業中に電話に出られないことが多い

# RFP（提案依頼書）がすでにある場合は、置いてから話しかける
cp ~/Downloads/提案依頼書.docx docs/00-inputs/rfp.docx
> RFP を置いたので始めて
```

前提：bash、Python 3.10+（`uv` があれば高速）、Node は不要。Word に図を画像で載せたい場合だけ `npm i -g @mermaid-js/mermaid-cli`。

### 既存のリポジトリに ZIP で導入する（README.md だけのリポジトリ向け）

[Releases](https://github.com/xim2jp/auto-requirement/releases) から `rfp-requirements-kit-v<版>.zip` を取得し、**リポジトリの直下に解凍する**だけで使える（README.md は同梱していないので上書きされない）。

```bash
cd my-repo                                   # README.md だけがあるリポジトリ
unzip ~/Downloads/rfp-requirements-kit-v2.0.0.zip
claude
> 作りたいシステムの説明（数行でよい）
```

- 解凍されるもの：`START_HERE.md`（利用者向けの「はじめに」）、`.claude/`（6 エージェント・4 Skill・hooks）、`CLAUDE.md`（PM 役の指示）、`docs/`（RFP の置き場と成果物の骨組み）、`deliverables/`、`.gitignore`、`PROJECT_LEARNINGS.md`、`.framework-version`、`.claude-manifest`
- `.claude` などの名前が「.」で始まるフォルダは、Mac の Finder では見えない（`Cmd + Shift + .` で表示）。Finder でコピーするより、上のように `unzip` で直接解凍するのが確実。Windows はエクスプローラーで「すべて展開」→ 中身をリポジトリ直下へ移動でよい
- Python 環境は、初めて Office を生成するときに `.venv/` へ自動で作られる（python3 が必要。要件定義の Markdown だけなら不要）
- 配布者向け：`bash scripts/build-kit.sh --test` で `dist/` に ZIP を作成し、README.md だけのダミーリポジトリで導入テストまで行う。`v*` タグを push すると GitHub Actions が同じ手順で ZIP を作り、Releases に添付する

### 既存のフォルダに導入する

```bash
cd existing-project
cp -r <このリポジトリ>/.claude ./
cp <このリポジトリ>/templates/project-init/{CLAUDE.md,PROJECT_LEARNINGS.md,setup.sh,.framework-version} ./
bash setup.sh
```

### Office 納品物だけを再生成する

```bash
bash .claude/skills/office-deliverables/scripts/build.sh all        # 生成＋機械検査
bash .claude/skills/office-deliverables/scripts/build.sh docx       # Word だけ
bash .claude/skills/office-deliverables/scripts/build.sh all --pdf  # LibreOffice があれば PDF も
bash .claude/skills/office-deliverables/scripts/build.sh extract    # RFP 原本（docx/xlsx/pptx）をテキスト化
```

## リポジトリ構造

```
.
├── .claude/
│   ├── agents/                         # 6 エージェント
│   │   ├── project-manager.md          #   PM（メインセッション）
│   │   ├── rfp-writer.md               #   Phase 0 構想の聞き取り・RFP 起草
│   │   ├── requirements-architect.md   #   Phase 1 RFP 分析・Phase 2 要件定義
│   │   ├── requirements-reviewer.md    #   Phase 3
│   │   ├── office-document-producer.md #   Phase 4
│   │   └── deliverable-reviewer.md     #   Phase 5
│   ├── skills/
│   │   ├── sdlc-toolkit/               # 共通契約（配置・Handoff・Verdict・修正ループ・PM プレイブック・文書セット）
│   │   ├── rfp-authoring/              # 構想 → RFP（非エンジニア向けの聞き取り・推奨値・RFP テンプレート）
│   │   ├── requirements-toolkit/       # 要件定義の方法論（IPA 準拠）・RFP 分析・テンプレート
│   │   └── office-deliverables/        # Office 生成・検査スクリプト、体裁基準、スライド構成仕様
│   ├── hooks/                          # 00-inputs・deliverables の保護、Verdict ブロック検査
│   └── settings.json
├── .claude-plugin/                     # plugin 配布（新規案件・試用向け）
├── skillfile/rfp-requirements/        # ライト版（単体スキル。SKILL.md 1 ファイル）
├── templates/kit/START_HERE.md         # 配布 ZIP に入れる利用者向けの「はじめに」
├── templates/project-init/             # 案件の初期化（setup.sh・CLAUDE.md・PROJECT_LEARNINGS.md・.framework-version・.mcp.json.example）
├── scripts/
│   ├── new-project.sh                  # 新規案件の作成
│   ├── update-project.sh               # 既存案件のフレームワーク更新（マニフェスト 3 分類）
│   ├── export-to-projects.sh           # 登録済み案件への一括配布
│   ├── collect-learnings.sh            # 案件の PROJECT_LEARNINGS 集約
│   ├── check-harness.sh                # エージェント・Skill・スクリプトの整合検査
│   ├── check-layout-drift.sh           # 成果物パスと artifact-layout の整合検査
│   ├── smoke-test.sh                   # new-project → setup → Office 生成の通し確認
│   └── build-kit.sh                    # 配布用 ZIP キットの作成（--test で導入テスト）
├── docs/
│   ├── operations/                     # 還流・バージョニング・互換性契約・ハーネス執筆ガイド
│   ├── learnings/                      # 案件から還流した知見
│   └── projects/                       # 案件レジストリ（配布先）
└── misc/                               # 参考資料
```

## 設計の要点

- **構想から RFP を作る**：非エンジニアの話を原文のまま記録し（concept.md）、選択肢と「おまかせ（推奨値）」付きの質問で RFP に仕上げる。推奨値で埋めた点は「（想定）」と前提 AS-NN として RFP に明記し、要件定義で必ず確かめる。規模に合わない厳しい条件は足さない
- **RFP が要件の起点**：RFP を 1 項目 1 要求の RFP-NNN に分解し、明確／曖昧／矛盾／欠落／対象外を判定。曖昧・矛盾・欠落はすべて OQ にして発注者に確認する。RFP 要求は黙って捨てず、全 RFP-NNN に行き先（BZ・UC・NFR・制約）か対象外の理由を付ける
- **方法論はフル版と同じ**：ビジネス要求（問題・課題 → 業務目的と測定尺度 → 手段 → 優先順位・採否）→ システム化要求（UC・NFR 6 カテゴリ・権限・用語）。記述規約（禁止語・MEDIC・一文一義）は reviewer が Grep で機械検査
- **納品物は生成する**：Markdown 正本 → Office。同じ正本から全納品物を作るので件数・ID・用語が一致する。発注者の指摘は Markdown を直して再生成し、版数を上げる
- **機械で守れることは hooks で守る**：`docs/00-inputs/`（RFP 原本）・`deliverables/`・`docs/01-rfp/extracted/` への手書き拒否、レビューレポートの Verdict ブロック必須
- **モデルは固定しない**：全エージェント `model: inherit`

## フル版との関係

設計・実装・テスト・運用まで扱うフル版（46 エージェント + 28 Skill）は有料での提供を予定している。本リポジトリはその要件定義工程を切り出した無償版で、要件定義の成果物はフル版にそのまま引き継げる。

| | フル版（派生元の全工程 SDLC フレームワーク） | 本フレームワーク |
|---|---|---|
| 範囲 | 企画・戦略 → 要件 → 設計 → 実装 → テスト → 運用（Phase 0〜21） | 構想 → RFP → 要件定義 → Office 納品（Phase 0〜5） |
| 起点 | 企画（Phase 1）。RFP は任意 | **構想（話すだけ）→ RFP を作成**。持ち込み RFP も可 |
| エージェント / Skill | 46 / 28 | 6 / 4 |
| 人間向け出力 | htmldocs（HTML） | **Word（要件定義要求書・要件定義書・付録文書）・Excel・PowerPoint** |
| 要件定義の成果物 | `docs/03-requirements/` | 同じ（互換）。後工程はフル版に引き継げる |

## 運用

- 案件の気付きは `PROJECT_LEARNINGS.md` に即日記録し、月次で本体に還流（`docs/operations/feedback-loop.md`・`monthly-review.md`）
- 本体の改善は `scripts/export-to-projects.sh` で登録案件へ配布（案件側のカスタマイズは `.claude-manifest` の 3 分類で保護）
- 改訂時は `bash scripts/check-harness.sh && bash scripts/check-layout-drift.sh && bash scripts/smoke-test.sh`（CI でも実行）

## ライセンス・利用条件

- [Apache License 2.0](LICENSE)。商用利用・改変・再配布は自由（著作権表示とライセンス文の同梱、変更点の明示が条件）
- 本ツールが生成する文書は下書きです。発注者に提出する前に、内容・数値・契約条件を必ず人が確認してください
