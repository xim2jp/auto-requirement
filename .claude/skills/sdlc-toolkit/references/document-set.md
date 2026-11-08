# 文書セット（プロファイルと Office 納品物の対応）

Phase 1 完了時に PM がユーザーと確定し、`docs/99-pm/document-set.md` に記録する。RFP が提出物（文書名・形式・部数）を指定していれば、その指定が最優先。

## 1. プロファイル

| 文書（docs/） | standard（既定） | light（小規模・PoC） | proposal（提案付き） |
|--------------|:---:|:---:|:---:|
| 01-rfp/concept.md・rfp.md（構想から作る案件） | ● | ● | ● |
| 01-rfp/rfp-analysis.md | ● | ● | ● |
| 03-requirements/requirements.md | ● | ●（§3・§7・§16・§17 は簡略可） | ● |
| business-requirements.md | ● | ● | ● |
| use-cases.md | ● | ●（記述は Critical UC のみ） | ● |
| non-functional.md | ● | ●（主要カテゴリのみ、他は「対象外（理由）」） | ● |
| permissions-matrix.md | ● | ○（ロール 2 つ以下なら requirements.md §11 に統合） | ● |
| glossary.md | ● | ● | ● |
| open-questions.md | ● | ● | ● |
| decision-log.md | ● | ● | ● |
| proposal.md | — | — | ● |

●必須　○任意　—作らない

## 2. Office 納品物

| 納品物 | standard | light | proposal |
|--------|:---:|:---:|:---:|
| 要件定義要求書（RFP）（.docx。構想から作る案件のみ） | ● | ● | ● |
| 要件定義書（.docx。本編） | ● | ● | ● |
| 付録文書（別紙 1〜7 の .docx。`appendix_mode: bundled` なら要件定義書に綴じ込み） | ● | ●（light で作らない文書の別紙は出ない） | ● |
| 要件一覧（.xlsx） | ● | ○ | ● |
| 要件定義サマリー（.pptx） | ● | ○ | ●（提案説明を含む構成） |

作らない納品物は `deliverable-profile.yaml` で `enabled: false` にする。

## 3. docs/99-pm/document-set.md の書式

```markdown
# 文書セット
- プロファイル：standard（理由：RFP の規模・提出物要求）
- 確定日：YYYY-MM-DD　承認：ユーザー

| 文書／納品物 | 採否 | 理由・備考 |
|-------------|------|-----------|
| use-cases.md | 採用 | |
| proposal.md | 除外 | RFP は要件定義書のみ要求 |
| 要件定義サマリー（.pptx） | 採用 | 承認会議で使用 |
```
