#!/bin/bash
# setup.sh - RFP Requirements Framework 初期セットアップ（RFP 起点の要件定義＋Office 納品物）

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# バージョンは .framework-version（正本: templates/project-init/.framework-version）から動的に読む。
# - new-project.sh 経由（FRAMEWORK_BOOTSTRAP=1）: カレントに配置済みの .framework-version を読む
# - standalone 実行: setup.sh と同じ場所（テンプレートディレクトリ）の .framework-version を読む
if [ -f ".framework-version" ]; then
  FRAMEWORK_VERSION=$(head -n 1 .framework-version | tr -d ' ')
elif [ -f "$SCRIPT_DIR/.framework-version" ]; then
  FRAMEWORK_VERSION=$(head -n 1 "$SCRIPT_DIR/.framework-version" | tr -d ' ')
else
  FRAMEWORK_VERSION="unknown"
fi

echo "🚀 RFP Requirements Framework セットアップ"
echo "   バージョン: $FRAMEWORK_VERSION"
echo ""

# FRAMEWORK_BOOTSTRAP=1 が設定されているときは new-project.sh から呼ばれており、ファイル配置は完了している。
if [ -z "$FRAMEWORK_BOOTSTRAP" ]; then
  if [ -d ".claude" ]; then
    echo "⚠️  既存の .claude/ ディレクトリが見つかりました"
    read -p "バックアップして上書きしますか？ (y/N): " confirm
    if [[ $confirm == [yY] ]]; then
      mv .claude ".claude.backup.$(date +%Y%m%d_%H%M%S)"
      echo "✅ バックアップ完了"
    else
      echo "❌ セットアップを中止しました"
      exit 1
    fi
  fi

  # .claude/ の場所を探す（standalone で setup.sh を置いた場合の親探索）
  if [ -d "$SCRIPT_DIR/../../.claude" ]; then
    cp -r "$SCRIPT_DIR/../../.claude" ./
  elif [ -d "$SCRIPT_DIR/../.claude" ] && [ "$SCRIPT_DIR/.." != "$HOME" ]; then
    # $HOME 配下の場合はユーザーのグローバル ~/.claude を誤コピーしてしまうため除外
    cp -r "$SCRIPT_DIR/../.claude" ./
  else
    echo "❌ .claude/ が見つかりません（FRAMEWORK_BOOTSTRAP=1 を付けて new-project.sh から実行してください）"
    exit 1
  fi
  echo "✅ .claude/ を配置"

  cp "$SCRIPT_DIR/CLAUDE.md" ./
  cp "$SCRIPT_DIR/PROJECT_LEARNINGS.md" ./
  cp "$SCRIPT_DIR/.framework-version" ./
  mkdir -p scripts
  cp "$SCRIPT_DIR/scripts/gen-manifest.sh" scripts/ 2>/dev/null || true
  chmod +x scripts/gen-manifest.sh 2>/dev/null || true
  echo "✅ テンプレートファイル配置"
else
  echo "✅ ファイル配置はスキップ（new-project.sh から呼び出されたため）"
fi

# .claude-manifest（配布時ハッシュ台帳）— bootstrap/standalone 両モードで生成
if [ -d ".claude" ] && [ ! -f ".claude-manifest" ]; then
  if [ -f "scripts/gen-manifest.sh" ]; then
    bash scripts/gen-manifest.sh
  else
    {
      echo "# .claude-manifest — フレームワーク配布ファイルのハッシュ台帳（compatibility-contract.md 準拠）"
      echo "# update-project.sh がカスタマイズ検出（3分類）に使用する。手動編集しない"
      echo "version: $FRAMEWORK_VERSION"
      find .claude -type f | LC_ALL=C sort | xargs -d '\n' sha256sum
    } > .claude-manifest
    echo "✅ .claude-manifest を生成"
  fi
fi

# docs/ 構造
echo ""
echo "📁 docs/ 構造を初期化..."
mkdir -p docs/{00-inputs/materials,01-rfp/extracted,01-rfp/reviews,03-requirements/reviews,04-deliverables/reviews,99-pm} deliverables tmp
for dir in docs/00-inputs/materials docs/01-rfp docs/03-requirements docs/04-deliverables docs/99-pm deliverables; do
  touch "$dir/.gitkeep"
done
echo "✅ docs/ 構造作成完了"

# docs/00-inputs/README.md（RFP の置き方）
if [ ! -f "docs/00-inputs/README.md" ]; then
  cat > docs/00-inputs/README.md << 'EOF2'
# docs/00-inputs/ — RFP と参考資料の置き場（Phase 0）

ここは**あなた（ユーザー）が資料を置く場所**です。エージェントはこのフォルダの資料を読みますが、書き換えません（`INDEX.md` だけをエージェントが更新します）。

| 置くもの | ファイル名（推奨） | 必須か |
|---------|------------------|--------|
| RFP（提案依頼書・要件定義依頼書・システム化企画書） | `rfp.md` / `rfp.docx` / `rfp.pdf` / `rfp.xlsx` など。複数ファイル可 | **必須** |
| 参考資料（現行の業務フロー・帳票・画面、議事録、規程、現行システムの資料） | `materials/` 配下 | 任意。あると現状把握が速くなります |

- Word・Excel・PowerPoint の RFP はそのまま置けます（エージェントがテキスト化して読みます）
- RFP がまだ無い場合は、雛形 `.claude/skills/requirements-toolkit/templates/rfp.md` をコピーして `rfp.md` を書くか、Claude Code に「RFP を一緒に作りたい」と話しかけてください
- RFP の改訂版を受け取ったら、旧版を残したまま版数付きのファイル名（`rfp_v2.docx` など）で追加してください

置いたら Claude Code で「RFP を置いたので始めて」と話しかけてください。

流れ：Phase 1 RFP 分析 →（確認）→ 2 要件定義（ヒアリング）→ 3 要件レビュー → 4 Office 成果物作成 → 5 成果物レビュー → 納品（`deliverables/` に Word・Excel・PowerPoint）
EOF2
  echo "✅ docs/00-inputs/README.md 配置"
fi

# 成果物プロファイルの雛形（文書情報は Phase 1 完了時に PM が確認して埋める）
if [ ! -f "docs/04-deliverables/deliverable-profile.yaml" ] && [ -f ".claude/skills/office-deliverables/templates/deliverable-profile.yaml" ]; then
  cp .claude/skills/office-deliverables/templates/deliverable-profile.yaml docs/04-deliverables/deliverable-profile.yaml
  echo "✅ docs/04-deliverables/deliverable-profile.yaml（雛形）配置"
fi

# .gitignore
if [ -f ".gitignore" ]; then
  if ! grep -q "tmp/" .gitignore; then
    cat >> .gitignore << 'EOF'

# Claude Code framework
tmp/
.venv/
.claude.backup.*/
EOF
    echo "✅ .gitignore 更新"
  fi
else
  cat > .gitignore << 'EOF'
.venv/
__pycache__/
tmp/
.env
.DS_Store
Thumbs.db
~$*
.vscode/
.idea/
.claude.backup.*/
EOF
  echo "✅ .gitignore 作成"
fi

# Python 環境（Office 納品物の生成・RFP 原本のテキスト化）
REQS=".claude/skills/office-deliverables/scripts/requirements.txt"
if [ -f "$REQS" ]; then
  echo ""
  echo "🐍 Office 生成用の Python 環境（.venv）を準備..."
  if [ ! -x ".venv/bin/python" ]; then
    if command -v uv >/dev/null 2>&1; then uv venv -q .venv; else python3 -m venv .venv; fi
  fi
  if command -v uv >/dev/null 2>&1; then
    uv pip install -q --python .venv/bin/python -r "$REQS" && echo "✅ .venv に依存ライブラリを導入（uv）" || echo "⚠️  依存の導入に失敗。後で build.sh が再試行します"
  else
    .venv/bin/python -m pip install -q -r "$REQS" && echo "✅ .venv に依存ライブラリを導入（pip）" || echo "⚠️  依存の導入に失敗。後で build.sh が再試行します"
  fi
  command -v mmdc >/dev/null 2>&1 || echo "ℹ️  図（Mermaid）を Word に画像で載せるには: npm i -g @mermaid-js/mermaid-cli（任意）"
fi

# status.md
TODAY=$(date +%Y-%m-%d)
if [ ! -f "docs/99-pm/status.md" ]; then
  cat > docs/99-pm/status.md << EOF
# プロジェクト進捗

- **プロジェクト名**: （未設定）
- **発注者**: （未設定）
- **開始日**: $TODAY
- **最終更新**: $TODAY
- **フレームワーク版**: $FRAMEWORK_VERSION
- **現在フェーズ**: Phase 0 / 5（RFP 配置待ち）
- **納品版数**: -
- **次のアクション**: docs/00-inputs/ に RFP を置き、Claude Code で「RFP を置いたので始めて」と話しかける

## フェーズ別ステータス

| Phase | 名称 | ステータス | 担当 | 成果物 | Verdict | ループ | 完了日 |
|-------|------|----------|------|--------|---------|-------|--------|
| 0 | RFP 配置（ユーザー） | ⏳ | （ユーザー） | docs/00-inputs/ | - | - | - |
| 1 | RFP 分析 | ⏳ | requirements-architect | docs/01-rfp/rfp-analysis.md, docs/00-inputs/INDEX.md | - | - | - |
| 2 | 要件定義 | ⏳ | requirements-architect | docs/03-requirements/ | - | - | - |
| 3 | 要件レビュー | ⏳ | requirements-reviewer | docs/03-requirements/reviews/ | - | - | - |
| 4 | Office 成果物作成 | ⏳ | office-document-producer | deliverables/, docs/04-deliverables/ | - | - | - |
| 5 | 成果物レビュー | ⏳ | deliverable-reviewer | docs/04-deliverables/reviews/ | - | - | - |

## 凡例: ⏳ 待機 / 🚧 進行中 / 🔄 レビュー中 / 🔁 再レビュー / ⛔ Block / ✅ 完了 / ⚠️ エスカレーション / 📦 納品済
## 「ループ」列: レビュー実行回数/上限5回（rework-loop.md 準拠。Block は自動で修正ループ、5回超えで PM エスカレーション）

## 納品履歴

| 版数 | 納品日 | 内容 | 発注者の反応 |
|------|--------|------|-------------|

## 未決事項（OQ）の推移

| 日付 | open | answered | closed | 備考 |
|------|------|----------|--------|------|

## エスカレーション履歴
（なし）

## リスク・課題
| ID | 内容 | 発生Phase | 影響 | 対応状況 |
|----|------|----------|------|---------|

## 意思決定ログ
（PM判断を記録）

## 還流ループ記録
| 日付 | アクション | 詳細 |
|------|----------|------|
| $TODAY | フレームワーク導入 | $FRAMEWORK_VERSION からスタート |
EOF
  echo "✅ docs/99-pm/status.md 初期化"
fi

# プロジェクト名入力
echo ""
echo "📝 プロジェクト情報を入力してください（後で編集可）"
read -p "プロジェクト名: " project_name || true
if [ -n "$project_name" ]; then
  if sed --version 2>/dev/null | grep -q GNU; then
    sed -i "s/<案件名をここに>/$project_name/" PROJECT_LEARNINGS.md
    sed -i "s/^- \*\*プロジェクト名\*\*: （未設定）/- **プロジェクト名**: $project_name/" docs/99-pm/status.md
  else
    sed -i "" "s/<案件名をここに>/$project_name/" PROJECT_LEARNINGS.md
    sed -i "" "s/^- \*\*プロジェクト名\*\*: （未設定）/- **プロジェクト名**: $project_name/" docs/99-pm/status.md
  fi
  echo "✅ PROJECT_LEARNINGS.md / status.md 更新"
fi

echo ""
echo "🎉 セットアップ完了！"
echo ""
echo "📂 配置されたファイル:"
echo "  - .claude/                  フレームワーク本体（5 エージェント + 3 Skill + hooks）"
echo "  - .framework-version        $FRAMEWORK_VERSION"
echo "  - CLAUDE.md                 Claude Code メインコンテキスト（PM 役）"
echo "  - PROJECT_LEARNINGS.md      案件知見の記録"
echo "  - docs/00-inputs/           ← ここに RFP を置く"
echo "  - deliverables/             Office 納品物の出力先（Word・Excel・PowerPoint）"
echo ""
echo "🚀 次のステップ:"
echo "  1. docs/00-inputs/ に RFP（.md / .docx / .xlsx / .pdf など）と参考資料を置く"
echo "  2. claude を起動"
echo "  3. 「RFP を置いたので始めて」と話しかける"
echo ""
echo "💡 気付きは PROJECT_LEARNINGS.md にその日のうちに記録し、月次で本体へ還流"
