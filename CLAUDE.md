# paddleocr-vl

## 版本发布流程

### 版本号管理

使用 `hatch-vcs` 从 git tag 自动推导版本号，无需手动维护版本字符串。

版本号的唯一来源是 **git tag**，格式为 `v<semver>`（如 `v0.3.0`）。

### 发布步骤

```bash
# 1. 改完代码，提交
git add -A
git commit -m "feat: xxx"

# 2. 打 tag
git tag v0.3.0

# 3. 推送（含 tag）
git push --tags origin master
```

### 升级机制

用户安装方式为 `uv tool install git+https://github.com/raawaa/paddleocr-vl.git`，升级时：

```bash
uv tool upgrade paddleocr-vl
```

`uv tool upgrade` 通过比较版本号决定是否重装，所以每次发布必须 bump tag。

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
