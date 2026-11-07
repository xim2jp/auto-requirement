#!/bin/bash
# init-repo.sh - フレームワーク本体リポジトリの初期化
# このスクリプトは、ZIPを展開した直後に1回だけ実行する

set -e

echo "🚀 RFP Requirements Framework リポジトリを初期化"
echo ""

# Git リポジトリ初期化
if [ -d ".git" ]; then
  echo "⚠️  既に .git/ が存在します"
  read -p "削除して再初期化しますか？ (y/N): " confirm
  if [[ $confirm == [yY] ]]; then
    rm -rf .git
  else
    echo "中止しました"
    exit 0
  fi
fi

git init -b main
echo "✅ Git リポジトリ初期化"

# .gitignore
cat > .gitignore << 'EOF'
# OS
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/

# 仮ファイル
*.tmp
*.bak
.claude.backup.*/
.venv/
__pycache__/
tmp/
misc/
EOF
echo "✅ .gitignore 作成"

# 初回コミット
git add .
git commit -m "Initial: RFP Requirements Framework $(head -n1 templates/project-init/.framework-version)

RFP 起点の要件定義と Office 納品物（Word・Excel・PowerPoint）の作成までを行う
Claude Code ハーネス（5 エージェント + 3 Skill + hooks）。
派生元の全工程 SDLC フレームワーク v0.18.0 から派生。詳細は README.md / CHANGELOG.md。
"

echo "✅ 初回コミット完了"

# タグ付け
V=$(head -n1 templates/project-init/.framework-version)
git tag -a "v$V" -m "Initial release"
echo "✅ v$V タグ作成"

echo ""
echo "🎉 初期化完了！"
echo ""
echo "次のステップ:"
echo ""
echo "1. GitHub でリポジトリを作成:"
echo "   https://github.com/new"
echo "   - リポジトリ名: rfp-requirements-framework"
echo "   - 公開範囲（Public / Private）を選択"
echo "   - README、.gitignore、ライセンスは作らない（既存のため）"
echo ""
echo "2. リモート設定とプッシュ:"
echo "   git remote add origin git@github.com:<your-username>/rfp-requirements-framework.git"
echo "   git push -u origin main"
echo "   git push --tags"
echo ""
echo "3. 最初の案件を作る:"
echo "   bash scripts/new-project.sh ~/projects/my-first-rfp"
echo ""
echo "詳しくは README.md を参照"
