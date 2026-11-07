# ROADMAP

## 近い将来（1.x）

- [ ] 実案件 1 件目で Phase 0〜5 を通し、ヒアリングの往復回数・納品物の手戻りを PROJECT_LEARNINGS に記録する
- [ ] 発注者指定の Word テンプレート（.dotx）・会社ロゴを表紙に差し込めるようにする（profile に `word.template` / `logo`）
- [ ] Excel 台帳の発注者による編集結果（ステータス・回答）を Markdown 正本へ取り込む逆方向の同期（OQ 回答の取り込みから）
- [ ] 提案書（proposal.md）を PowerPoint の提案説明デッキとして出す標準構成
- [ ] Mermaid 図を mmdc なしで画像化する手段の検討（Kroki 等。社外送信の可否を含めて判断）

## 中期

- [ ] RFP 分析の自動補助：RFP 原本の章節構造から RFP-NNN の候補表を機械生成し、requirements-architect が判定する
- [ ] 版間差分レポート（第 0.9 版 → 第 1.0 版で変わった要件の一覧）を Word の変更履歴付き文書として出す
- [ ] フル版（派生元の全工程 SDLC フレームワーク）への引き継ぎスクリプト（`docs/03-requirements/` と RFP 分析をフル版案件に移す）

## 方針

- 範囲は要件定義まで。設計以降はフル版で行う
- 納品物は Markdown 正本からの生成を貫く（Office ファイルを手で直す運用にしない）
