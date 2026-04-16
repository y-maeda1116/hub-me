# Dynamic GitHub Profile README Design

## Overview

GitHub Actions を使用して `y-maeda1116/hub-me` リポジトリの README.md を動的に更新する。毎日深夜0時に実行され、プロフィール統計カード、リポジトリステータス、最近のコミット、技術傾向を自動反映する。

## Architecture

```
hub-me/
├── .github/
│   └── workflows/
│       └── profile-cards.yml    # 毎日深夜0時に全実行する単一ワークフロー
├── scripts/
│   ├── update_readme.py         # README テンプレートの動的セクション更新
│   ├── fetch_repo_status.py     # 指定リポジトリのRelease/Build status取得
│   └── analyze_commits.py       # 過去1週間のコミット解析→技術傾向サマリ
├── profile-cards/               # github-profile-summary-cards が生成するSVG
├── docs/
│   └── superpowers/
│       └── specs/
│           └── 2026-04-17-dynamic-readme-design.md
└── README.md                    # テンプレート化されたREADME
```

## Components

### 1. GitHub Actions Workflow (`profile-cards.yml`)

- **トリガー**: cron (`0 15 * * *` = JST 深夜0時) + push to main + workflow_dispatch
- **権限**: `contents: write` (コミット用)
- **実行順序**:
  1. `vn7n24fzkq/github-profile-summary-cards` Action で SVG 生成 → `profile-cards/`
  2. `fetch_repo_status.py` でリポジトリステータス取得
  3. `analyze_commits.py` でコミット解析
  4. `update_readme.py` で README テンプレートの各セクション更新
  5. 変更があれば git commit & push

### 2. fetch_repo_status.py

**入力**: GITHUB_TOKEN, リポジトリリスト (環境変数 or 引数)
**出力**: JSON (標準出力)

対象リポジトリ:
- Weekly-Task-Board
- security-base
- my-github-config
- apple-refurb-discord-notify

各リポジトリについて取得:
- リポジトリ名
- 最新 Release タグ (なければ "N/A")
- 最新ワークフローランステータス (success/failure/N/A)

`gh api` を使用:
- `repos/{owner}/{repo}/releases/latest` → タグ名
- `repos/{owner}/{repo}/actions/runs?per_page=1` → ステータス

### 3. analyze_commits.py

**入力**: GITHUB_TOKEN, 過去7日間のコミットログ
**出力**: テキスト (標準出力)

処理:
1. `gh api` で `repos/{owner}/{repo}/commits?since={7_days_ago}` を全リポジトリ分取得
2. コミットメッセージとファイル拡張子から技術スタックを推定
3. 技術別コミット数を集計
4. 上位技術を短文でサマライズ

技術推定ルール:
- `.go` → Go
- `.tf`, `.hcl` → Terraform
- `.py` → Python
- `.ts`, `.tsx` → TypeScript
- `.js`, `.jsx` → JavaScript
- `Dockerfile`, `.yml` (workflow) → Docker/CI
- その他 → 拡張子マッピング辞書

### 4. update_readme.py

**入力**: README.md テンプレート, 各スクリプトの出力
**出力**: 更新された README.md (ファイル上書き)

テンプレートタグ:
- `<!-- PROFILE_CARDS -->` ... `<!-- /PROFILE_CARDS -->` → SVG 画像リンク
- `<!-- REPO_STATUS_TABLE -->` ... `<!-- /REPO_STATUS_TABLE -->` → リポジトリ表
- `<!-- RECENT_COMMITS -->` ... `<!-- /RECENT_COMMITS -->` → 最新3コミット
- `<!-- CURRENT_FOCUS -->` ... `<!-- /CURRENT_FOCUS -->` → 技術傾向

処理:
1. README.md を読み込む
2. 正規表現でタグ間のコンテンツを置換
3. ファイルに書き戻す

### 5. README.md テンプレート

```markdown
# y-maeda1116

<!-- PROFILE_CARDS -->
![Stats](profile-cards/stats.svg)
![Languages](profile-cards/languages.svg)
<!-- /PROFILE_CARDS -->

## Repository Status

<!-- REPO_STATUS_TABLE -->
<!-- /REPO_STATUS_TABLE -->

## Recent Activity

<!-- RECENT_COMMITS -->
<!-- /RECENT_COMMITS -->

## Current Focus

<!-- CURRENT_FOCUS -->
<!-- /CURRENT_FOCUS -->
```

## Constraints

- 外部API・サードパーティサービス不使用
- `GITHUB_TOKEN` + `gh` CLI のみ使用
- 画像はリポジトリ内の相対パス (CDN不使用)
- Python スクリプトは標準ライブラリ + `subprocess` で `gh` CLI を呼び出し
- 外部 pip パッケージへの依存なし

## Error Handling

- `gh api` がレートリミット or エラーの場合 → 既存セクションを保持 (空で上書きしない)
- Release なしリポジトリ → "N/A" を表示
- ワークフローランなしリポジトリ → "N/A" を表示
- コミット0の週 → "No activity this week" を表示

## Testing

- 各Pythonスクリプトに `--dry-run` フラグでローカルテスト可能に
- `workflow_dispatch` で手動実行可能
