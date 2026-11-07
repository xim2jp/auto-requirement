# summary-deck.yaml の仕様（要件定義サマリー）

`docs/04-deliverables/summary-deck.yaml` は PowerPoint の**スライド構成**を書くファイルである。デザイン（配色・フォント・配置・ページ番号・フッター）はスクリプトが付けるので、ここには**何を、どの順で、どの結論で**見せるかだけを書く。

## 1. 全体

```yaml
title: 要件定義サマリー            # 表紙タイトル（省略時は profile の powerpoint.kind）
subtitle: 〇〇システム更改に向けた要件定義の結果と、ご判断いただきたい事項
agenda: true                      # 章扉（section）が 2 つ以上あれば目次スライドを自動挿入
slides:
  - type: section
    title: 背景と目的
  - type: bullets
    title: プロジェクトの目的
    message: 受付業務の処理時間を 1 件 15 分から 5 分に削減することが目的です
    bullets:
      - text: 現状、受付 1 件に平均 15 分（月 1,200 件・延べ 300 時間）
        children:
          - 紙の申込書を基幹システムへ二重入力している（RFP-004）
      - text: 達成目標 OBJ-01：受付処理時間 5 分以内（2027 年 9 月）
        bold: true
    notes: 話者ノート。説明の補足や想定問答
    source: 要件定義書 §1・別紙1 BZ-001   # ノート末尾に「出典：」として入る
```

全スライド共通の項目：`title`（名詞句、20 字以内）、`message`（キーメッセージ＝結論の 1 文、40 字以内。タイトル直下に強調表示）、`notes`、`source`。

## 2. スライド型

| type | 用途 | 固有の項目 |
|------|------|-----------|
| `section` | 章扉。番号は自動（01, 02 …） | `title`、`message`（任意） |
| `bullets` | 箇条書き。最大 2 階層 | `bullets`：文字列、または `{text, bold, children}` |
| `kpi` | 数値の強調（件数・目標値・効果） | `items`：`{label, value, sub}` を 2〜6 個 |
| `table` | 表。9 行を超えると自動で複数枚に分割 | 直接指定：`columns` と `rows`。正本から引用：`from`（下記） |
| `two_column` | 2 案比較・論点整理 | `left` / `right`：`{heading, bullets}` |
| `before_after` | 現状と実現後の対比（決裁者向け） | `before` / `after`（箇条書き）、`before_heading` / `after_heading` |
| `steps` | スケジュール・進め方（3〜6 段） | `steps`：`{label, period, bullets}`、`current`（強調する段の番号 0 始まり） |
| `closing` | 今後の進め方・お願い事項 | `bullets`、`contact`（連絡先の枠） |

### 表の正本引用（`from`）

数値・ID の手入力は転記ミスの元になる。台帳の表は Markdown 正本から引く。

```yaml
  - type: table
    title: 未決事項（ご判断のお願い）
    message: 3 件は 11 月 20 日までのご判断が必要です
    from:
      file: open-questions.md       # docs/01-rfp/ または docs/03-requirements/ のファイル名
      id_prefix: OQ-                # 1 列目がこの接頭辞で始まる行を集める
      columns: [ID, 内容, 決まらない場合の影響, 期限]   # 列名は前方一致・部分一致で探す
      filter: {column: ステータス, equals: open}        # または in: [open, deferred]
      limit: 12
```

## 3. 要件定義サマリーの標準ストーリー（12〜16 枚）

決裁者が「何が決まり、何を判断すればよいか」を 15 分で掴めることを狙う。

| # | 型 | タイトル例 | キーメッセージの書き方 |
|---|----|-----------|----------------------|
| 1 | （表紙・目次は自動） | | |
| 2 | section | 背景と目的 | |
| 3 | bullets / before_after | 現状の問題と目指す姿 | 問題を定量で 1 文（〇〇に月 N 時間） |
| 4 | kpi | 達成目標 | OBJ と測定尺度・目標値 |
| 5 | section | 要件定義の結果 | |
| 6 | kpi | 要件の全体像 | RFP 要求 N 件を BZ N 件・UC N 件・NFR N 件に整理 |
| 7 | table（from rfp-analysis.md） | RFP 要求への対応 | 対象外・先送りにした要求があればここで明示 |
| 8 | table（from business-requirements.md） | 業務要件（採用分） | Must の件数と範囲 |
| 9 | bullets / table | スコープ（対象と対象外） | 「やらないこと」を同じ重みで |
| 10 | table（from use-cases.md） | 主要ユースケース | 業務領域と Critical UC |
| 11 | table（from non-functional.md） | 非機能要件の主要値 | 可用性・性能・セキュリティの数値 |
| 12 | section | ご判断いただきたい事項 | |
| 13 | table（from open-questions.md, open） | 未決事項 | 期限と、決まらない場合の扱い |
| 14 | kpi / table | 投資と効果の概算 | 推奨（着手／縮小／棚上げ） |
| 15 | steps | 今後の進め方 | 承認 → 基本設計 → … |
| 16 | closing | お願い事項 | 回答期限・承認手続き |

## 4. 書き方の規律

- 1 枚 1 メッセージ。キーメッセージを読めば本文を読まなくても結論が分かる
- 箇条書きは 6 項目まで、1 項目 40 字程度まで。超えるならスライドを分ける（文字が多いとスクリプトが自動で縮小し、最小 11pt でも収まらなければ build-stats.json に警告が出る）
- 数値・ID は Markdown 正本と一致させる。表は `from` で引く
- 社内用語（エージェント名・Phase 番号・ファイルパス）を書かない。文書は「要件定義書 §3」「別紙2 ユースケース一覧」の呼び名で参照する
- 未決・対象外・リスクを隠さない。決裁者が後で驚く情報ほど前に出す
