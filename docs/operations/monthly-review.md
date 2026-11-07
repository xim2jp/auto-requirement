# 月次レビュー手順

毎月最終金曜（または月末日）の所要時間：30分〜1時間

## 事前準備（5分）

```bash
# 本体リポジトリへ移動
cd ~/rfp-requirements-framework

# 最新化
git pull origin main

# 案件レジストリ確認
cat docs/projects/INDEX.md
```

## ステップ1: 各案件の LEARNINGS を集約（15分）

各案件で：

```bash
cd ~/projects/saas-project-A
cat PROJECT_LEARNINGS.md  # 確認

# または集約スクリプト使用
cd ~/rfp-requirements-framework
bash scripts/collect-learnings.sh
```

集約スクリプトは各案件の LEARNINGS.md を本体の `docs/learnings/YYYY-MM-collected.md` にまとめる（オプション）。

## ステップ2: 還流候補の抽出（10分）

各 LEARNING について判断：

| 質問 | 判定 |
|------|------|
| 他案件でも起こりうるか？ | Yes → 還流候補 |
| 既存エージェント・Skillの修正で対応可？ | Yes → patch / minor |
| 新規追加が必要？ | Yes → minor / major |
| セキュリティ・重大バグか？ | Yes → 即時対応 |

## ステップ3: GitHub Issue 作成（10分）

還流候補ごとに：

```bash
gh issue create \
  --template framework-improvement.md \
  --title "[improvement] xxx エージェントに XXX を追加" \
  --label "improvement"
```

または GitHub UI で：
1. リポジトリ → Issues → New issue
2. 「Framework Improvement」テンプレ選択
3. テンプレに従って記入

## ステップ4: 優先順位付け（5分）

Issues を眺めて：

- 🔴 **Critical**: セキュリティ・重大バグ → 即対応
- 🟡 **High**: 複数案件で必要 → 今月中
- 🟢 **Medium**: あると便利 → 来月以降
- ⚪ **Low**: 将来的にやる → backlog

## ステップ5: PR作成・マージ（時間に応じて）

Critical / High から：

```bash
# 機能ブランチ作成
git checkout -b improvement/agent-xxx

# 該当ファイル修正
vim .claude/agents/xxx.md

# CHANGELOG 更新
vim CHANGELOG.md
# - 新規追加した行（## [unreleased] セクション）

# コミット・PR
git add .
git commit -m "improvement: xxx エージェントに XXX を追加"
git push origin improvement/agent-xxx
gh pr create --fill
```

PR テンプレに従い、影響範囲・関連Issue番号を記入。

## ステップ6: リリースタグ（PRマージ後）

月内に複数のPRがマージされたら、まとめてリリース：

```bash
git checkout main
git pull origin main

# バージョン判定
# - patch (0.0.x): 既存改善のみ
# - minor (0.x.0): 新規エージェント・Skill追加
# - major (x.0.0): 破壊的変更

NEW_VERSION="v0.1.1"  # 例

# CHANGELOG の [unreleased] を [v0.1.1] に書き換え
vim CHANGELOG.md

# タグ作成
git tag -a $NEW_VERSION -m "Release $NEW_VERSION"
git push origin $NEW_VERSION

# GitHub Release 作成
gh release create $NEW_VERSION \
  --title "$NEW_VERSION" \
  --notes-file <(sed -n "/## \[$NEW_VERSION\]/,/## \[/p" CHANGELOG.md | head -n -1)
```

## ステップ7: 既存案件への通知（5分）

各案件の現バージョンを `docs/projects/INDEX.md` で確認し、影響を判定：

```markdown
# Project Registry

| 案件名 | 現在バージョン | 最終更新 | 次回更新予定 |
|--------|-------------|---------|------------|
| saas-A | v0.1.0     | 2026-05-15 | v0.1.1 推奨 |
| saas-B | v0.1.0     | 2026-05-10 | v0.1.1 推奨 |
```

影響案件は次回作業時にアップデート判断。

## ステップ8: 振り返り記録（5分）

`docs/learnings/YYYY-MM-monthly-review.md` に：

```markdown
# 月次レビュー: YYYY-MM

## 今月の活動
- 各案件のLEARNINGS確認件数：
- 還流PR数：
- 新バージョンリリース：

## 良かった点
- 

## 改善点
- 

## 来月の重点
- 
```

## チェックリスト

レビュー完了時：

- [ ] 全案件のLEARNINGSを確認した
- [ ] 還流候補を Issue 化した
- [ ] Critical/High 優先のものは PR を作った
- [ ] CHANGELOG.md を更新した
- [ ] 新バージョンタグを作った（PR があれば）
- [ ] docs/projects/INDEX.md を更新した
- [ ] 振り返りを docs/learnings/ に残した

## サボったときの自己対策

「今月忙しくてレビューできなかった」場合：

1. 翌週でいいから、必ず実施
2. 2ヶ月連続で飛ばしたら警報。「フレームワーク運用が破綻している」サイン
3. 案件数を増やす前に、運用を見直す

## 自動化アイデア（将来）

- GitHub Actions で月末に Issue 自動作成（「月次レビュー実施を」）
- 各案件の LEARNINGS.md の更新日を集約するスクリプト
- バージョン乖離が大きい案件の自動検出
