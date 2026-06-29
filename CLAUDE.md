# paddleocr-vl

## 版本发布流程

### 版本号管理

使用 `hatch-vcs` 从 **git tag** 自动推导版本号，无需手动维护版本字符串。

版本号的唯一来源是 git tag，格式为 `v<semver>`（如 `v0.2.1`）。

`src/paddleocr_vl/__init__.py` 通过 `importlib.metadata.version("paddleocr-vl")` 动态读取版本号，构建时从最近的 git tag 衍生。

### 发布清单

```bash
# 1. 提交代码（确保所有改动已 commit）
git add -A
git commit -m "feat/sync/chore: xxx"

# 2. 打 tag（决定版本号）
git tag v0.3.0

# 3. 推送到 GitHub（含 tag）
git push --tags origin master
```

> 如果 tag 打错了需要重打：`git tag -d v0.3.0 && git push origin :refs/tags/v0.3.0`

### 版本号规则

| 场景 | 示例 tag | 衍生产出的版本 |
|------|----------|----------------|
| 正式发布 | `v0.3.0` | `0.3.0` |
| tag 后有新 commit | （无 tag） | `0.3.1.dev0+g<sha>.d<date>` |

### 用户升级方式

用户安装方式为 `uv tool install git+https://github.com/raawaa/paddleocr-vl.git`：

```bash
# 常规升级（版本号比较）
uv tool upgrade paddleocr-vl

# 强制重装（忽略版本号，拉取最新 commit）
uv tool install git+https://github.com/raawaa/paddleocr-vl.git --reinstall
```

`uv tool upgrade` 通过比较版本号决定是否重装，所以每次发布**必须 bump tag**。

### 源码目录

```
src/paddleocr_vl/
├── __init__.py    # 通过 importlib.metadata.version() 动态读取版本号
├── __main__.py    # python -m 入口
├── api.py         # API 调用（submit_job, poll_job, download_result）
├── cli.py         # argparse CLI 入口
├── config.py      # 配置文件读写（~/.config/paddleocr-vl/config.json）
├── errors.py      # 自定义异常
└── parser.py      # JSONL 结果解析为 Markdown
```

### 依赖管理

- 使用 `uv` 管理项目环境
- 新增依赖用 `uv add requests`（正式依赖）或 `uv add --dev pytest`（开发依赖）
- 不要用 `pip install` 或 `uv pip install` 装项目依赖

## Agent skills

### Issue tracker

GitHub issues in `raawaa/paddleocr-vl` (via `gh`); external PRs are not a triage surface. See `docs/agents/issue-tracker.md`.

### Triage labels

Default vocabulary (each role's label string equals its name): `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout: one `CONTEXT.md` + `docs/adr/` at the repo root (created lazily). See `docs/agents/domain.md`.
