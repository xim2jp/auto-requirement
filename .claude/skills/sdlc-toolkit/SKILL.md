---
name: sdlc-toolkit
description: 構想（または持ち込み RFP）起点の要件定義 SDLC（Phase 0〜5：RFP 準備→RFP 分析→要件定義→要件レビュー→Office 成果物→成果物レビュー）の共通契約。成果物の配置、Handoff / Self-Check / Verdict の書式、修正ループ、文書セット、執筆ルールを 1 か所に定める。全エージェントが frontmatter の skills でプリロードする。「成果物の配置」「フェーズ進行」「レビュー手順」「修正ループ」で参照。
---

# SDLC Toolkit — 全エージェント共通契約

この Skill は全エージェントにプリロードされる。ここに書いてあることは各エージェント定義で繰り返さない。詳細は `references/` にあり、必要なときに開く。

## 1. 全体像

このハーネスの範囲は**要件定義まで**である。ユーザーは非エンジニアであることを前提にする。ユーザーが話す「作りたいシステムの概要・全体像」から RFP（要件定義要求書）を作り（ユーザーが RFP を持っていればそれを使う）、その RFP を起点に要件を定義・合意し、Microsoft Office の納品物（要件定義要求書・要件定義書・付録文書・要件一覧・要件定義サマリー）として出す。

```
0 RFP 準備：構想の聞き取り → RFP 起草 →〔ユーザー確認：RFP の要点〕（RFP を持っていれば配置だけ）
→ 1 RFP 分析 →〔ユーザー確認：案件概要・文書セット・成果物プロファイル〕
→ 2 要件定義（ヒアリング）→ 3 要件レビュー ⇄ 修正ループ
→ 4 Office 成果物作成 → 5 成果物レビュー ⇄ 修正ループ →〔PM 納品判定〕→ 納品
→ 発注者の指摘・変更要求 → 2 に戻り版数を上げて再納品
```

| Phase | 名称 | producer | reviewer |
|------:|------|----------|----------|
| 0 | RFP 準備（構想 → RFP） | rfp-writer（持ち込み RFP ならユーザーが配置） | （PM がユーザー確認） |
| 1 | RFP 分析 | requirements-architect | （PM がユーザー確認） |
| 2 | 要件定義 | requirements-architect | — |
| 3 | 要件レビュー | — | requirements-reviewer |
| 4 | Office 成果物作成 | office-document-producer | — |
| 5 | 成果物レビュー | — | deliverable-reviewer |

基本設計以降（画面・データ・開発・テスト・運用）は**後工程**であり、このハーネスでは扱わない。後工程に渡す成果物は `docs/03-requirements/`（パス・ID 体系は 派生元の全工程 SDLC フレームワーク の Phase 5 成果物と互換）。担当・ゲートの詳細は `references/pm-playbook.md` が正本。

## 2. 成果物の置き場

`references/artifact-layout.md` が正本（パスは安定 API）。

| 場所 | 中身 | 書き手 |
|------|------|--------|
| `docs/00-inputs/` | ユーザーの持ち込み資料（RFP 原本・構想メモ・参考資料）。`INDEX.md` だけエージェントが書ける（hook が強制） | ユーザー |
| `docs/01-rfp/` | `concept.md`（構想の聞き取り記録）・`rfp.md`（作成した RFP の正本）は rfp-writer。`rfp-analysis.md`（RFP-NNN 分解）は requirements-architect。`extracted/`（原本のテキスト化）はスクリプト | rfp-writer／requirements-architect |
| `docs/03-requirements/` | 要件定義の正本（Markdown） | requirements-architect |
| `docs/04-deliverables/` | 成果物プロファイル・スライド構成・機械検査レポート | office-document-producer |
| `deliverables/` | Office 納品物（.docx / .xlsx / .pptx）。スクリプトの生成物で手書き不可（hook が強制） | スクリプト |
| `docs/99-pm/` | status.md・document-set.md | project-manager |

- レビューは `docs/<phase-dir>/reviews/YYYY-MM-DD-<agent>-loopN.md`、producer の指摘対応表は同じ場所に `-response-loopN.md`
- 作る文書は `docs/99-pm/document-set.md` で案件ごとに決まる。除外された文書の不存在は指摘しない
- 既存ファイルがあれば上書きせず節を更新する。RFP 原本を書き換えて矛盾を吸収しない

## 3. RFP との整合

RFP は発注者の一次情報であり、要件定義の判断の根拠である。RFP の正本は、持ち込みなら `docs/00-inputs/` の原本、構想から作った案件なら `docs/01-rfp/rfp.md`（ユーザー確認済みの版）。Phase 2 以降の全員は `docs/01-rfp/rfp-analysis.md` を読み、自分の成果物が RFP 要求（RFP-NNN）と矛盾しないようにする。

- RFP の矛盾・曖昧・欠落を独断で解釈しない。OQ（種別：RFP 矛盾／RFP 曖昧／RFP 欠落）を起票し、仮決めと根拠を書いて発注者の判断を待つ
- RFP 要求を黙って捨てない。対象外・先送りにする要求は理由付きで rfp-analysis.md と decision-log に残す
- RFP の全要求を MUST にしない。優先順位と採否は要件定義で決め、発注者の合意を取る
- 発注者に RFP の改訂を求めるべき事項は Handoff の「発注者確認事項（RFP 改訂候補）」で PM に返す。作成した RFP（`docs/01-rfp/rfp.md`）の改訂は、PM がユーザーの了承を得てから rfp-writer が版を上げて行う（要件側の都合で黙って書き換えない）

## 4. producer の提出書式

成果物の末尾に **Self-Check → Handoff** の順で付ける（Office 納品物では自動で除かれる）。Self-Check が無い成果物はレビュワーが差し戻してよい（ループ回数は消費しない）。

```markdown
## ✅ Self-Check
- 実施日: YYYY-MM-DD
- 結果: N/M pass（fail は理由を書く。隠して pass にしない）
| # | 項目 | 判定 | 備考 |

## 📤 Handoff
- **Created by**: <agent>  - **Date**: YYYY-MM-DD
- **Next suggested agent(s)**: ...
- **Open questions for next phase**: ...
- **Assumptions made**: ...
- **発注者確認事項（RFP 改訂候補）**: （無ければ「なし」）
- **Files referenced**: ...
```

Self-Check の項目は自エージェント定義の「品質基準」節から作る。

## 5. reviewer の判定と書式

- Severity は Critical / Major / Minor / Nit。**Critical ≥1 → Block、Major のみ → Warning、それ以外 → Approve**。指摘ゼロも正当な結果
- 指摘には該当箇所・失敗モード・根拠を付ける。根拠が出せないものは書かない。重要度を膨らませない
- レビュワーは成果物本体を直さない。Write は自分のレポートだけ
- 2 回目以降は producer の対応表を照合する。対応表なし・無変更再提出（NO-CHANGE）は Block
- レポート末尾と完了報告の両方に **Verdict ブロック**を置く（PM が機械的に読む。hook が検査する）：

```
VERDICT: BLOCK | WARNING | APPROVE
LOOP: N/5
RETURN_TO: <修正担当エージェント名>（APPROVE 時は NEXT_PHASE）
REPORT: docs/<phase-dir>/reviews/YYYY-MM-DD-<reviewer>-loopN.md
```

レポートの節構成は `references/review-protocol.md`。

## 6. 修正ループ

Block が出たら PM は確認なしで `RETURN_TO` のエージェントを修正モードで起動し、producer は Critical / Major 全件に「修正済／代替案／反論（根拠）／保留」を付けた対応表を書き、レビュワーを再起動する。上限 5 回。5 回目でも Block なら PM がエスカレーション（発注者確認／Defer 付き承認／スコープ見直し）。Warning はユーザーに「修正」か「受容（Defer 記録）」を確認する。詳細は `references/rework-loop.md`。

修正モードで起動された producer は、レビューレポートを読み、指摘に触れずに再提出しない。

## 7. 執筆ルール（docs/ 配下の全文書）

docs/ の Markdown はそのまま Office 納品物になる。発注者が読む文章として書く。

- 冒頭に「この文書について」（目的・読者・前提）。**最初の 1 文**は発注者が読んで分かる文にする（Word の別紙冒頭に使われる）
- ID と名称を併記する（`UC-SIGNUP-01 新規登録`）。指示代名詞（あれ・それ・上記の）で参照しない
- 用語は `docs/03-requirements/glossary.md` に合わせる。一文一義、数値で書く（`requirements-toolkit/references/writing-rules.md`）
- ID 台帳は 1 列目を `ID` 列にした Markdown 表で書く（Excel 台帳の抽出キー）。同じ種類の表は同じ列名にする
- 本文に作業痕跡を残さない：エージェント名・Phase 番号・ファイルパスは Self-Check / Handoff / reviews にだけ書く。本文で他文書を指すときはファイル名（`use-cases.md`）で書けば納品物では「別紙2「ユースケース一覧」」に置き換わる
- 文書間の整合（同じ ID に同じ名称、参照先の実在）は書き手の責任

## 8. 受注側の前提（チームごとに書き換える）

受注者として要件定義を行う場合の前提。**発注者（RFP）の条件が常に優先**し、RFP に記載が無いものは OQ にする。以下は既定値であり、利用するチームの体制・得意分野・契約方針に合わせて書き換える。

- **体制**：要件定義は少人数＋AI で行う想定。ヒアリングは発注者の担当者経由。1 ターン 3 問まで
- **後工程を自社で受ける場合**：自社の標準技術スタックと運用体制で守れない SLA（例：99.99%・24 時間対応）を約束しない。支払条件・契約形態などの自社の制約は、見積・契約条件の検討にだけ使い、要件には混ぜない
- **品質姿勢**：過剰品質とスコープクリープを警戒し、やらないことを明記する。決まらない要件は隠さず、中止・棚上げも選択肢に入れる

## 9. ユーザーとの話し方（非エンジニア前提）

ユーザーに見せる文（PM の報告・中継する質問・RFP の要点）は、専門用語と ID を使わずに書く。成果物（docs/・Office）の中は従来どおり正式な用語と ID で書く。

- **質問は 1 回 3 問まで**。全問に選択肢と「おまかせ（推奨：…）」「分からない」を付け、なぜ聞くかを 1 行添える。「分からない」には推奨値で仮定して進み、仮定は成果物に明記する（OQ・AS）
- **報告は結論から、数字で**。「業務要件 18 件」ではなく「やりたいこと 18 項目を整理しました（うち必須 9）」
- **判断を求めるときは選択肢 2〜3 個とおすすめ**を示し、それぞれ「何が変わるか」を 1 行で書く
- 言い換え（ユーザーへの文で使う語）：

| 成果物での用語 | ユーザーへの言い方 |
|--------------|----------------|
| RFP（要件定義要求書） | 依頼内容のまとめ（RFP） |
| 要件定義 | システムに求めることを、作る人に誤解なく伝わる形に決める作業 |
| 業務要件（BZ）／ユースケース（UC） | やりたいこと／システムでできること（操作の流れ） |
| 非機能要件（NFR） | 速さ・止まらなさ・安全性・サポートなどの条件 |
| ロール・権限（ROLE） | 使う人の種類と、それぞれができること |
| 要確認事項（OQ） | 決めていただきたいこと（期限つき） |
| 前提・仮定（AS） | こちらで仮に決めたこと（あとで変えられます） |
| MoSCoW（Must／Should／Could） | 必須／できれば／余裕があれば |
| 稼働率・RTO・RPO | 止まってよい時間・復旧までの時間・巻き戻ってよいデータの範囲 |
| 移行 | 今のデータを新しいシステムに移すこと |

## 10. references

| ファイル | 内容 |
|---------|------|
| `references/pm-playbook.md` | フェーズ表（担当・成果物・ゲート）、status.md 書式、文書セット、納品判定、変更要求 |
| `references/artifact-layout.md` | `docs/`・`deliverables/` のディレクトリ構造と命名、ID 体系 |
| `references/review-protocol.md` | レビュー姿勢、Severity 定義、レポート書式 |
| `references/rework-loop.md` | 修正ループと対応表、エスカレーション、差し戻し先表 |
| `references/document-set.md` | 文書セットのプロファイル（標準／軽量／提案付き）と Office 納品物の対応 |
