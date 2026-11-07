# ハーネス執筆ガイド（agents / skills / hooks / MCP / plugin）

このフレームワークの `.claude/` 配下は、Claude Code の **Fable 5.1 / Opus 5.5 世代**を前提に書く。旧世代向けの「手順を一歩ずつ指示し、禁止事項を繰り返して縛る」書き方は捨て、**役割・入出力・品質基準・判断の軸**を簡潔に渡す。モデルは与えられた目的と制約から手順を自分で組める。この文書は、エージェント定義と Skill を新設・改訂するときの正本である。

## 1. 設計原則

1. **一度だけ書く**。全エージェント共通の作法（成果物の置き場、Handoff、Self-Check、Verdict、修正ループ、オーナー制約）は `sdlc-toolkit/SKILL.md` にだけ書き、各エージェントは frontmatter の `skills:` で読み込む。エージェント本文で共通作法を再説明しない。
2. **意図と不変条件を書き、手順は書かない**。「第 1 パスで A、第 2 パスで B」のような段取りは不要。何を達成するか、何が満たされていなければ Block か、どこで迷ったら誰に聞くか、を書く。
3. **機械で守れることは hooks で守る**。`docs/00-inputs/` の読み取り専用、レビューレポートの Verdict ブロック必須、は `.claude/settings.json` の hooks が強制する。プロンプトで「絶対禁止」を繰り返さない。
4. **履歴を書かない**。「v0.8.0 で追加」のような版数注記は CHANGELOG の仕事。プロンプトには現在の仕様だけを書く。
5. **描写は短く、判断材料は厚く**。ドメインのチェック観点・Block 条件・固有ノウハウは残す。言い換え・強調・重複は削る。
6. **モデルは固定しない**。`model: inherit` を既定にし、操作者が選んだモデルで動かす。コスト上の理由で下位モデルに固定したいときだけ案件側で上書きする。
7. **信頼する**。モデルは文脈を読み、必要な参照を自分で開く。「必読」「必ず Read」は、読まないと成果物が壊れる入力に限って書く。

## 2. エージェント定義のテンプレート

```markdown
---
name: <kebab-case。ファイル名と一致。改名は破壊的変更>
description: <1〜3 文、300 字以内。何をする／いつ使う／起動語。版数注記を書かない>
model: inherit
skills:
  - sdlc-toolkit
  - <ドメイン Skill があれば>
tools: <レビュワーなど制限が必要な場合のみ。省略＝全ツール継承>
---

# <役割名>

<1〜3 段落：この役割は何に責任を持ち、どんな姿勢で臨むか。設計者としての裁量と、上流を勝手に変えない線引き>

## 入力
<読むべき成果物のパス。判断の根拠になる正本（RFP 原本・rfp-analysis・requirements）と、自フェーズの直接入力>

## 成果物
<出力パスと、その文書の骨子（見出しレベルの構成）。テンプレが Skill にあればパスだけ>

## 品質基準
<この役割の成果物が満たすべきこと。レビュワーなら Block / Major の判定条件。producer なら Self-Check 項目になる観点>

## 判断の軸
<裁量を発揮する場面と、ユーザーや PM に確認すべき場面。運用者（受注側）固有の制約がこの役割でどう効くか>

## 連携
<誰から受け取り、誰に渡すか。Handoff の Next suggested agent(s)>
```

目安：**150 行・8KB 以内**。超えるなら、知識部分を Skill の references に移す。

### 書いてよいこと／書かないこと

| 書く | 書かない |
|------|---------|
| 成果物パス（安定 API） | 共通作法の再説明（Handoff / Self-Check / Verdict の書式） |
| ドメインのチェック観点・Block 条件 | 「第 N パス」などの実行手順 |
| 固有ノウハウ（Stripe の端数処理、LIFF の制約など） | 版数注記（v0.x で追加） |
| 判断の軸・トレードオフ | 「必読」「絶対禁止」の反復 |
| 連携先エージェント名 | 他エージェントの責務の説明 |

### frontmatter の決め方

- `model: inherit` を既定。PM・レビュワーも同じ（操作者が上位モデルを選べば自動で上がる）
- `skills:` に `sdlc-toolkit` を必ず入れる（全文がプリロードされる。SKILL.md は 150 行以内に保つ）。ドメイン Skill は 1〜2 本まで
- `tools:` はレビュワーのみ `Read, Grep, Glob, Write`（＋必要なら Bash / WebSearch）で絞る。producer・specialist・PM は省略して全ツールを継承する（PM はサブエージェント起動のため `Agent` が必要）
- `effort` / `maxTurns` / `memory` は原則使わない。使うなら理由を本文に書く

## 3. Skill のテンプレート

```markdown
---
name: <kebab-case。ディレクトリ名と一致>
description: <何の知識集か＋どの場面で参照するか＋起動語。400 字以内>
---

# <Skill 名>

<2〜3 段落：この領域で一貫して守る原則。運用者固有の判断があればここ>

## 参照ファイル
| ファイル | 内容 | いつ読むか |

## 原則
<番号付き、1 項目 1〜2 行。各項目は「なぜ」を含む>

## アンチパターン
<箇条書き。実際に起きた失敗を優先>
```

- SKILL.md は **500 行以内**。深い知識は `references/`、雛形は `templates/`、実行物は `scripts/` に置く
- 「エージェント別の使い方ガイド」節は書かない（各エージェント定義が自分の入出力を知っている。重複は乖離の元）
- `paths:` を使うと、該当ファイルに触れたときだけ自動ロードされる（例：`supabase/**` で `local-dev-environment`）
- `context: fork` は「調査して結果だけ返す」型の Skill に使う（知識集には使わない）

## 4. hooks（機械で守る不変条件）

`.claude/settings.json` に登録。スクリプトは `.claude/hooks/` に置き、`${CLAUDE_PROJECT_DIR}` で参照する。

| hook | 守る不変条件 | 挙動 |
|------|------------|------|
| `guard-inputs.sh`（PreToolUse: Write/Edit） | `docs/00-inputs/` は INDEX.md 以外書き換え禁止。`deliverables/`（Office 納品物）と `docs/01-rfp/extracted/` は生成物なので手書き禁止 | exit 2 で拒否し理由を返す |
| `check-review-report.sh`（PostToolUse: Write） | `reviews/*-loopN.md` に Verdict ブロック 4 行が揃っている | 欠けていれば `decision: block` で書き直しを促す |

hooks は依存ゼロの bash で書く。新しい不変条件を足すときは「プロンプトで言い続けるより hook で守れるか」を先に考える。

## 5. MCP サーバー

- 常時接続は増やさない（ツール定義がコンテキストを食う）。登録は作業単位で付け外す
- 案件に配布する雛形は `templates/project-init/.mcp.json.example`。トークンは `${VAR}` 展開で環境変数から読み、コミットしない
- 特定エージェントだけが使うサーバーは、エージェント frontmatter の `mcpServers:` に名前で書ける（案件の `.mcp.json` に定義がある前提）
- 要件定義では原則 MCP を常用しない。RFP・参考資料がクラウドストレージにある場合だけ、そのコネクタを付ける

## 6. plugin 配布

`.claude-plugin/plugin.json` と `marketplace.json` により、コピー配布（`update-project.sh`）に加えて `claude plugin install` でも配れる。ただし plugin 経由のエージェント名は `rfp-requirements-framework:project-manager` のように名前空間が付くため、`RETURN_TO:` を素の名前で解決している既存案件はコピー配布のままにする。plugin 配布は新規案件・試用向け。

## 7. 改訂時のチェック

`bash scripts/check-harness.sh` が frontmatter の必須項目、office-deliverables スクリプトの存在と構文、`model: inherit` と `skills: sdlc-toolkit` の有無、description 長、版数注記の残存、サイズ超過、rework-loop の差し戻し先の実在を検査する。`scripts/check-layout-drift.sh`、`scripts/smoke-test.sh`（new-project → setup → Office 生成の通し確認）と合わせて CI で走る。Office 生成スクリプトを変えたら smoke-test に加えて、実際の Word / Excel / PowerPoint で開いて PDF 化し、ページ画像で崩れを確認する（`office-deliverables/references/office-style-guide.md` §5）。
