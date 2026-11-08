# Office 納品物の体裁基準（日本の業務文書）

「そのまま発注者に出せる」かどうかの判断基準。生成スクリプトが満たす項目（✓自動）と、書き手（Markdown・YAML）が満たす項目（✎書き手）を分けて示す。deliverable-reviewer はこの文書を判定基準に使う。

## 1. 共通

| 観点 | 基準 | 担保 |
|------|------|------|
| 文書情報 | 案件名・発注者・作成者・文書番号・版数・発行日・機密区分が全ファイルで一致 | ✓自動（profile） |
| 版管理 | 改訂履歴に今回の版と変更内容がある。再提出時は版数を上げる | ✎profile.revisions |
| 作業痕跡 | エージェント名・Phase 番号・`docs/` パス・YYYY-MM-DD・〈…〉・TODO・「（記入）」・`...` が無い | ✎Markdown（check が WARN） |
| 用語 | 用語集の正式名称で統一。同じものを別名で呼ばない | ✎Markdown |
| 参照 | 「上記」「それ」ではなく「§3.1」「BZ-003 締め作業の短縮」のように章節番号・ID＋名称で参照 | ✎Markdown |
| 数値 | 単位・桁区切り・全角半角が統一（金額は ¥1,200,000 または 120 万円、どちらかに統一） | ✎Markdown |
| 未決 | 未決事項は隠さず OQ 一覧で明示し、本文にも「OQ-003 で確認中」と書く | ✎Markdown |

## 2. Word（要件定義書）

| 観点 | 基準 | 担保 |
|------|------|------|
| 前付け | 表紙 → 承認欄 → 改訂履歴 → 目次。目次は見出し 2 レベルまで | ✓自動 |
| ヘッダー／フッター | ヘッダー左に機密区分、右に文書名｜案件名。フッターに文書番号・ページ x / y・作成者 | ✓自動 |
| 見出し | 章番号付き。見出しだけがページ末尾に残らない（次段落と同じページ） | ✓自動 |
| 本文 | 本文は明朝 10.5pt、見出しはゴシック。一文 100 字以内を目安、200 字超は分割 | ✓フォント／✎文長 |
| 表 | ヘッダー行が色付きで改ページ時に繰り返す。1 文字ずつ縦に折り返す列が無い。8 列以上は横向きページ | ✓自動（列名・値を短くするのは✎） |
| 図 | 業務フロー・状態遷移・データモデルは図として見える（Mermaid は mmdc で画像化） | ✓mmdc 導入時 |
| 別紙 | 別紙ごとに改ページし、冒頭 1 文で内容を説明 | ✓自動（1 文目は✎） |
| 社内節 | Self-Check・Handoff が含まれない | ✓自動 |

## 3. Excel（要件一覧）

| 観点 | 基準 | 担保 |
|------|------|------|
| 構成 | 表紙・目次（リンク）・集計・台帳・トレーサビリティ | ✓自動 |
| 台帳 | 見出し行固定・オートフィルタ・折返し・列幅調整・縞模様。1 シート 1 種類の ID | ✓自動 |
| 入力規則 | MoSCoW・採否・ステータス・判定の列は候補から選ぶ（既存値が候補外なら付けない） | ✓自動（値を候補に揃えるのは✎） |
| 集計 | COUNTIF 数式で台帳と連動。件数が Word・PowerPoint と一致 | ✓自動 |
| トレーサビリティ | BZ × UC の対応（UC を持たない BZ は色付け）、RFP 要求 → 対応 ID（未対応行は色付け） | ✓自動（対応 ID を書くのは✎） |
| 印刷 | A4 横・幅 1 ページ・見出し行の繰返し・ヘッダー／フッター | ✓自動 |

## 4. PowerPoint（要件定義サマリー）

| 観点 | 基準 | 担保 |
|------|------|------|
| 構成 | 表紙 → 目次 → 章扉 → 本文 → 今後の進め方。12〜16 枚 | ✎deck.yaml |
| メッセージ | 全本文スライドにキーメッセージ（結論 1 文）。タイトルは名詞句 | ✎deck.yaml |
| 文字量 | 箇条書き 6 項目・1 項目 40 字程度まで。本文 14pt 以上が目安（最小 11pt） | ✓縮小／✎分量 |
| 表 | 9 行まで（超過は自動分割）。列は 5 列程度まで | ✓分割／✎列選択 |
| 数値 | 表・KPI は正本から引く（`from`）。手入力した数値は正本と照合 | ✎deck.yaml |
| ノート | 説明者が読む補足と出典をノートに | ✎deck.yaml |

## 5. 目視確認の手順

機械検査は形式しか見ない。表の折返し・空白ページ・はみ出しはページ画像でしか見つからない。

**LibreOffice がある場合**：`build.sh all --pdf` で `deliverables/*.pdf` ができる。

**WSL＋Windows の Microsoft Office がある場合**（最も忠実）：Windows 側の一時フォルダにコピーし、PowerShell から各アプリで PDF 化する。

```powershell
# C:\Users\Public\office-check\topdf.ps1（引数：フォルダ）
param([string]$dir)
Get-ChildItem $dir -Filter *.docx | % { $w=New-Object -ComObject Word.Application; $d=$w.Documents.Open($_.FullName,$false,$true)
  $d.TablesOfContents | % { $_.Update() }; $d.ExportAsFixedFormat(($_.FullName -replace '\.docx$','.pdf'),17); $d.Close($false); $w.Quit() }
Get-ChildItem $dir -Filter *.xlsx | % { $x=New-Object -ComObject Excel.Application; $x.DisplayAlerts=$false; $b=$x.Workbooks.Open($_.FullName)
  $b.ExportAsFixedFormat(0,($_.FullName -replace '\.xlsx$','.pdf')); $b.Close($false); $x.Quit() }
Get-ChildItem $dir -Filter *.pptx | % { $p=New-Object -ComObject PowerPoint.Application; $s=$p.Presentations.Open($_.FullName,$true,$false,$false)
  $s.SaveAs(($_.FullName -replace '\.pptx$','.pdf'),32); $s.Close(); $p.Quit() }
```

```bash
mkdir -p /mnt/c/Users/Public/office-check && cp deliverables/*.{docx,xlsx,pptx} /mnt/c/Users/Public/office-check/
/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -NoProfile -ExecutionPolicy Bypass \
  -File 'C:\Users\Public\office-check\topdf.ps1' 'C:\Users\Public\office-check'
```

PDF はページ画像にして Read で見る（例：`.venv/bin/pip install pymupdf` → `page.get_pixmap(dpi=60).save(...)`）。全ページを 1 枚ずつ見るより、4〜8 ページを 1 枚に並べた一覧画像で崩れを探し、怪しいページだけ拡大する。画像・PDF は `tmp/` に置き、納品物に混ぜない。

## 6. 納品前チェックリスト

- [ ] check-report.md が FAIL 0。WARN は全件に判断（対応／許容の理由）がある
- [ ] 全ファイル（要件定義要求書・要件定義書・別紙・要件一覧・サマリー）の案件名・版数・発行日・件数（BZ・UC・NFR・OQ）が一致
- [ ] Word：目次が更新され、全見出しが載っている。空白ページ・1 文字折返しの列が無い
- [ ] Excel：全台帳の件数が Markdown と一致。トレーサビリティの色付き行（対応漏れ候補）に説明がつく
- [ ] PowerPoint：全本文スライドにキーメッセージ。文字あふれ・表のはみ出しが無い
- [ ] 作業痕跡（エージェント名・Phase・パス・書きかけ表記）が無い
- [ ] 機密区分・発注者名・宛名（御中）が正しい
