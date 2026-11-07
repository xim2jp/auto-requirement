---
name: office-deliverables
description: 要件定義の Markdown 正本から、発注者に納品できる Microsoft Office 成果物（Word 要件定義書・Excel 要件一覧・PowerPoint 要件定義サマリー）を生成・検査する。RFP 原本（docx/xlsx/pptx）のテキスト化も行う。成果物プロファイル・スライド構成の書き方、日本のビジネス文書の体裁基準、機械検査と目視確認の手順を収録。「Word にして」「Excel で一覧」「説明資料」「納品物」「成果物を作る」「RFP を読み込む」で参照。
---

# Office Deliverables — 要件定義の納品物を Office で出す

Markdown（`docs/01-rfp/`・`docs/03-requirements/`）が**正本**、Office ファイル（`deliverables/`）は正本から機械生成する**納品物**である。納品物の誤りは Markdown を直して再生成する。Office ファイルを手で直すと次の再生成で消え、正本との食い違いが残る（`deliverables/` への Write/Edit は hook が拒否する）。

## 1. 3 つの納品物

| 納品物 | 読み手と用途 | 構成 | 出典 |
|-------|-------------|------|------|
| **要件定義書**（.docx） | 発注者の担当・決裁者。合意と承認の正式文書 | 表紙 → 承認欄・改訂履歴 → 目次 → 本編（requirements.md）→ 別紙 1〜7（BZ・UC・NFR・ROLE・用語・OQ・RFP 分析） | requirements.md ほか全文書 |
| **要件一覧**（.xlsx） | 発注者・開発側の担当。要件の管理台帳・突合・進捗確認 | 表紙 → 目次 → 集計（数式連動）→ ID 台帳（RFP・BZ・UC・NFR・ROLE・IF・SH・用語・OQ・D）→ トレーサビリティ（RFP → BZ → UC） | 各文書の ID 付きの表 |
| **要件定義サマリー**（.pptx） | 決裁者・関係者。説明会・承認会議で 15〜20 分で説明 | 表紙 → 目次 → 章扉 → 結論ファーストの本文スライド → 今後の進め方 | `docs/04-deliverables/summary-deck.yaml` |

## 2. 使い方

```bash
# RFP 原本（docx/xlsx/pptx）を docs/01-rfp/extracted/ にテキスト化（Phase 1 の最初）
bash .claude/skills/office-deliverables/scripts/build.sh extract
# 3 種を生成し、機械検査まで（Phase 4）。--pdf で LibreOffice があれば PDF も
bash .claude/skills/office-deliverables/scripts/build.sh all
# 個別生成／検査のみ
bash .claude/skills/office-deliverables/scripts/build.sh docx|xlsx|pptx|check
```

初回は `.venv/` を作り `scripts/requirements.txt`（python-docx・openpyxl・python-pptx・markdown-it-py・PyYAML）を入れる。setup.sh でも導入される。

## 3. 入力ファイル（`docs/04-deliverables/`）

| ファイル | 書く人 | 内容 | テンプレ |
|---------|--------|------|---------|
| `deliverable-profile.yaml` | office-document-producer（値はユーザー確認） | 案件名・発注者・作成者・文書番号・版数・機密区分・承認欄・改訂履歴・配色・フォント・別紙構成・Excel シート構成 | `templates/deliverable-profile.yaml` |
| `summary-deck.yaml` | office-document-producer | スライド構成（型・キーメッセージ・箇条書き・表の出典・ノート） | `templates/summary-deck.yaml`、書き方は `references/deck-spec.md` |
| `check-report.md`／`build-stats.json` | スクリプト | 機械検査の結果と生成統計 | — |

`summary-deck.yaml` が無いと件数・BZ/UC 一覧・未決 OQ だけの既定構成になる。納品用には必ず書く。

## 4. 生成の仕組み（Markdown をどう書けば Office がきれいになるか）

- **見出し**：requirements.md の `##` が Word の見出し 1、別紙は「別紙N タイトル」が見出し 1 で文書内の `##` が見出し 2。番号は Markdown の見出し文字列をそのまま使う
- **前書き**：各文書の H1 と最初の `##` より前（「この文書について」・作成日など）は本文から除き、表紙と承認欄に置き換える。別紙の冒頭には「この文書について」の**最初の 1 文**だけを説明として残す。だから 1 文目は発注者が読んで分かる文にする
- **社内向けの節**：見出しに `Self-Check`・`Handoff` を含む節は納品物から除く（`output.strip_internal_sections`）
- **ファイル名の置換**：本文中の `business-requirements.md` などは「別紙1「業務要件一覧」」に、`requirements.md` は「本書」に置き換わる
- **表**：ヘッダー行の色・繰返し・縞・列幅の自動配分。8 列以上の表は見出しごと横向きページに置く。表は 1 列目を ID にする（Excel 台帳の抽出キー）
- **Excel 台帳**：シート定義の `id_prefix` で始まる 1 列目を持つ行を文書全体から集める。列名は括弧内の補足を無視して揃え、列構成が大きく違う表（目的系 BZ と手段系 BZ など）は別シートにする。MoSCoW・採否・ステータス・判定の列には入力規則と色分けが付く
- **Mermaid**：`mmdc`（@mermaid-js/mermaid-cli）があれば画像化、無ければソース枠で載る。発注者向けには画像化を推奨（`--mermaid npx` で npx 経由の取得も可）
- **禁止**：Markdown の HTML タグで体裁を作らない（無視される）。ASCII アートの図は Word では等幅の枠になる

## 5. 体裁の基準（`references/office-style-guide.md`）

日本の業務文書として「そのまま発注者に出せる」水準を基準にする。要点：

- 表紙・承認欄・改訂履歴・目次・ヘッダー（機密区分・文書名）・フッター（文書番号・ページ x / y・作成者）が揃っている
- 社内用語・作業痕跡が無い：エージェント名、Phase 番号、`docs/` パス、YYYY-MM-DD、〈…〉、TODO、「（記入）」
- スライドは 1 枚 1 メッセージ。タイトルは名詞句、キーメッセージは結論の 1 文。本文は 6 行・1 行 40 字程度まで、表は 9 行まで（超えると自動で分割）
- 数値・ID・用語は Markdown 正本と一致する（再生成で担保。手入力しない）

## 6. 検査（Phase 4 の producer と Phase 5 の reviewer が使う）

1. **機械検査**：`build.sh all`（または `check`）が `docs/04-deliverables/check-report.md` を書く。FAIL（ファイル欠落・目次なし・台帳件数の不一致）は必ず直す。WARN（書きかけ表記・社内用語・未定義 ID・UC の無い BZ・文字あふれ懸念）は 1 件ずつ要否を判断する
2. **目視確認**：PDF にしてページ画像を見る。LibreOffice があれば `--pdf`。WSL で Windows の Office がある場合は `references/office-style-guide.md` §5 の PowerShell 手順で Word/Excel/PowerPoint 自身に PDF 化させる（再現性が最も高い）。レイアウト崩れ（表の 1 文字折返し・空白ページ・あふれ）はページ画像でしか見つからない
3. 直すのは Markdown か YAML。生成スクリプト自体の不具合は PM に報告する

## 7. references / templates

| ファイル | 内容 |
|---------|------|
| `references/office-style-guide.md` | 日本の業務文書の体裁基準（Word・Excel・PowerPoint 別）、納品前チェックリスト、PDF 化と目視確認の手順 |
| `references/deck-spec.md` | `summary-deck.yaml` の仕様（スライド型・項目・表の出典指定）と、要件定義サマリーの標準ストーリー |
| `templates/deliverable-profile.yaml` | 成果物プロファイルの雛形（全項目と既定値の説明） |
| `templates/summary-deck.yaml` | 要件定義サマリーの標準構成（12〜16 枚） |
| `scripts/` | `build.sh`（入口）・`office_build.py`（生成 CLI）・`extract_inputs.py`（RFP 原本のテキスト化）・`docx_builder.py`・`xlsx_builder.py`・`pptx_builder.py`・`check.py`・`mdparse.py`・`profile.py`・`common.py` |
