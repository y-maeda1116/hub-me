# Language Versions per Repository

各リポジトリで利用している言語のバージョン一覧（2026-11-23 時点）。
バージョンは各リポジトリの `package.json` / `go.mod` / `pyproject.toml` 等の宣言値。

## TypeScript / Node

| Repository | TypeScript | Node (engines) | 備考 |
|---|---|---|---|
| [29cm-less-than-30](https://github.com/y-maeda1116/29cm-less-than-30) | ^7.0.2 | — | |
| [Weekly-Task-Board](https://github.com/y-maeda1116/Weekly-Task-Board) | ^5.9.3 | >=26.0.0 | 5.9残置、昇格条件は ROADMAP_TYPESCRIPT.md |
| [cam-cheat-sheet](https://github.com/y-maeda1116/cam-cheat-sheet) | typescript6@6.0.3 | >=22.12.0 | npmエイリアス構成 |
| [divination-journal](https://github.com/y-maeda1116/divination-journal) | ~5.9.3 | — | |
| [FlowPrint](https://github.com/y-maeda1116/FlowPrint) | ^5.8.3 | — | |
| [go-shichi-go](https://github.com/y-maeda1116/go-shichi-go) | ^7.0.2 | — | |
| [habit-tracker-pwa](https://github.com/y-maeda1116/habit-tracker-pwa) | ^6.0.3 | >=24.0.0 | |
| [kuku19-master](https://github.com/y-maeda1116/kuku19-master) | ^6.0.0 | — | |
| [nihon-no-shiro](https://github.com/y-maeda1116/nihon-no-shiro) | typescript6@^6.0.2 | >=22.12.0 | npmエイリアス構成 |
| [pack-and-go](https://github.com/y-maeda1116/pack-and-go) | ^5.6.0 | — | |
| [sumida-stream-coffee](https://github.com/y-maeda1116/sumida-stream-coffee) | ^5.8.3 | ^22.12.0 \|\| ^24.0.0 \|\| >=26.0.0 | |
| [toil-buster-cli](https://github.com/y-maeda1116/toil-buster-cli) | typescript6@^6.0.2 | >=24.0.0 | npmエイリアス構成 |
| [tokyo-hidden-transfers](https://github.com/y-maeda1116/tokyo-hidden-transfers) | ^7.0.0 | >=22.12 | |
| [ts-template-base](https://github.com/y-maeda1116/ts-template-base) | typescript6@^6.0.2 | >=22.22.1 | テンプレート |

### JavaScript (TypeScript なし)

| Repository | 備考 |
|---|---|
| [games](https://github.com/y-maeda1116/games) | Jest 29 / Playwright 1.65 |
| [Playful-Learning-Hub](https://github.com/y-maeda1116/Playful-Learning-Hub) | |
| [kaminarimon-lunch-map](https://github.com/y-maeda1116/kaminarimon-lunch-map) | |
| [math-training-kids](https://github.com/y-maeda1116/math-training-kids) | HTML/CSS/JS |
| [floral-fire-5c9c](https://github.com/y-maeda1116/floral-fire-5c9c) | Astro 5.1.3 |

## Go

| Repository | go.mod |
|---|---|
| [bean-watcher](https://github.com/y-maeda1116/bean-watcher) | 1.26.4 |
| [discord-trans-helper](https://github.com/y-maeda1116/discord-trans-helper) | 1.22 |
| [jre-green-trip](https://github.com/y-maeda1116/jre-green-trip) | 1.26.1 (tools/sync) |
| [security-base](https://github.com/y-maeda1116/security-base) | 1.26.1 (tools/sync) |
| [template-go-cross](https://github.com/y-maeda1116/template-go-cross) | 1.26.0 |
| [tenki-fuku-bot](https://github.com/y-maeda1116/tenki-fuku-bot) | 1.26.0 |
| [yutai-dashboard](https://github.com/y-maeda1116/yutai-dashboard) | 1.25.0 |
| [apple-refurb-discord-notify](https://github.com/y-maeda1116/apple-refurb-discord-notify) | 1.26 (go_version/) |

## Python

| Repository | requires-python |
|---|---|
| [ops-ai-agent](https://github.com/y-maeda1116/ops-ai-agent) | >=3.13 |
| [python-template-base](https://github.com/y-maeda1116/python-template-base) | >=3.13 |
| [security-base](https://github.com/y-maeda1116/security-base) | >=3.13 |
| [apple-refurb-discord-notify](https://github.com/y-maeda1116/apple-refurb-discord-notify) | python_version/requirements.txt |

## その他

| Repository | 言語 | 備考 |
|---|---|---|
| [terraform-aws-golden-path](https://github.com/y-maeda1116/terraform-aws-golden-path) | Terraform (HCL) | required_version >= 1.13 |
| [dotfiles](https://github.com/y-maeda1116/dotfiles) / [my-github-config](https://github.com/y-maeda1116/my-github-config) (アーカイブ) | Shell | |
| private-memo / til / daily-growth-extractor / databricks-test | (言語ファイルなし) | ドキュメント中心 |

## 集計

- **TypeScript**: 14 リポジトリ（TS 7.x: 3 / TS 6.x: 5 / TS 5.x: 6）
- **Go**: 8 リポジトリ（1.26 系が中心、discord-trans-helper のみ 1.22）
- **Python**: 3 リポジトリ（すべて >=3.13 で統一）
