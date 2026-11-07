# Version Strategy（バージョニング方針）

セマンティックバージョニング（SemVer）に準拠。

## 形式

`v<MAJOR>.<MINOR>.<PATCH>` 例: `v0.1.0`

## レベル判定

### MAJOR（x.0.0）：破壊的変更

以下のいずれか：

- エージェント間の連携プロトコル変更（Handoff Block の形式変更など）
- 既存エージェントの責務の大幅変更（依頼内容が変わる）
- 成果物配置（artifact-layout）の変更
- 旧版との非互換

**例**：v1.0.0 → v2.0.0
- Phase 構造を 12 → 15 に拡張
- エージェント名のリネーム

### MINOR（0.x.0）：機能追加（後方互換）

以下のいずれか：

- 新エージェント追加
- 新 Skill 追加
- 既存エージェントへの新機能追加（既存動作は維持）
- 新しい参照ファイル追加

**例**：v0.1.0 → v0.2.0
- `analytics-specialist` エージェント追加
- `magic-link` プロバイダのサポート追加

### PATCH（0.0.x）：小さな改善

以下のいずれか：

- 既存エージェントのプロンプト改善
- アンチパターンへの追記
- 誤字修正・表記揺れ
- チェックリストの項目追加
- 例の追加

**例**：v0.1.0 → v0.1.1
- `payment-integration-specialist` のチェックリストに項目追加
- `oauth-providers.md` の LINE 設定手順をより詳細化

## プレリリース（v1.0.0 まで）

現在は `v0.x.y` 系。`v1.0.0` 到達条件：

- 3案件以上で運用実績
- 還流ループが2サイクル以上回った
- 既存案件への配信プロセスが確立
- ドキュメントが整っている

それまでは API（エージェント仕様）の変更余地を残す。

## 案件側のバージョン追従

各案件は独立したペースでアップデート：

| 状況 | アクション |
|------|----------|
| Critical PATCH（セキュリティ） | 即取り込み |
| 重要 MINOR（新エージェント） | 次フェーズ着手時に取り込み |
| 小さい PATCH | 任意 |
| MAJOR | 案件単位で判断（取り込まない選択肢もあり） |

`.framework-version` ファイルで現バージョンを記録：

```
# プロジェクトルートの .framework-version
v0.1.0

# Phase 1 開始時に取り込み
# 案件固有のカスタマイズあり：
# - .claude/agents/auth-integration-specialist.md（LINE設定追加）
```

## CHANGELOG.md フォーマット

[Keep a Changelog](https://keepachangelog.com/) 準拠：

```markdown
# Changelog

## [Unreleased]

### Added
- 

### Changed
- 

### Deprecated
- 

### Removed
- 

### Fixed
- 

### Security
- 

## [v0.1.1] - 2026-05-31

### Added
- xxx

## [v0.1.0] - 2026-05-16

### Added
- Initial release: 21 agents + 7 skills
```

## タグの命名

- `v0.1.0`：通常リリース
- `v0.1.0-alpha.1`：プレリリース
- `v0.1.0-rc.1`：リリース候補

タグ作成は `scripts/release.sh` で自動化（オプション）。

## ブランチ戦略

シンプルな運用：

- `main`: 安定版、各リリースはここからタグ
- `improvement/<topic>`: 機能ブランチ、PRでmainへマージ
- `hotfix/<topic>`: Critical用、即マージ
- リリースブランチは作らない（規模が小さいため）

## バージョン管理ファイル

```
.
├── package.json（オプション）                      # version フィールド
├── CHANGELOG.md                                    # 変更履歴
├── templates/project-init/.framework-version      # ★バージョン正本（single source of truth）
└── docs/projects/INDEX.md                          # 各案件のバージョン記録
```

### バージョン正本ルール

**`templates/project-init/.framework-version` が唯一のバージョン正本**。スクリプト類はここから動的に読むため、リリース時にスクリプトの修正は不要：

- `scripts/new-project.sh` … 正本をそのまま新規案件にコピー
- `scripts/update-project.sh` … 正本から `LATEST_VERSION` を取得
- `templates/project-init/setup.sh` … 配置済み（またはテンプレートディレクトリの）`.framework-version` を読む

### リリース時チェックリスト

- [ ] `templates/project-init/.framework-version` を新バージョンに更新（正本）
- [ ] `CHANGELOG.md` に変更内容を記録
- [ ] `README.md` の「バージョン」節を更新
- [ ] `docs/projects/INDEX.md` の「バージョン乖離トラッキング」の最新版を更新
- [ ] `ROADMAP.md` のマイルストーンを更新
- [ ] git タグ付け（`v0.x.y`）

## 案件と本体のバージョン乖離

許容範囲：

- 1 minor 以内：問題なし
- 2 minor 以上：要見直し（取り込まない理由を明文化 or 取り込み）
- 1 major 以上：案件単位で再評価

`docs/projects/INDEX.md` で乖離を追跡。
