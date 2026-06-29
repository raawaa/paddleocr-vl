# paddleocr-vl

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

[English](README.md) | [中文](README.zh.md)

使用 [PaddleOCR-VL-1.6](https://github.com/PaddlePaddle/PaddleOCR) 百度 API 将
PDF（本地文件、远程 URL 或整个目录）转换为 Markdown 的 CLI 工具。

**先了解限额再开始**：API 大约每天免费 2 万页额度，超额返回 HTTP 429；单个
PDF 超过 100 页会被悄悄丢弃。详细行为见 `docs/troubleshooting.md`。

## 快速开始

```bash
# 1. 安装
uv tool install git+https://github.com/raawaa/paddleocr-vl.git

# 2. 配置 token（一次性）
paddleocr-vl config set-token "你的_token"

# 3. 转换
paddleocr-vl convert report.pdf
```

一次转换通常耗时 5 秒到 2 分钟——stderr 上有 spinner，完成时打印作业耗时与
字符数。Markdown 文件生成在输入同目录的 `report.md`。

> **环境要求：** Python 3.10+，以及在
> [aistudio.baidu.com/paddleocr](https://aistudio.baidu.com/paddleocr)
> 申请的 PaddleOCR API token。

## 使用示例

```bash
# 单个 PDF — input.pdf → input.md
paddleocr-vl convert report.pdf

# 远程 URL — 无需本地下载
paddleocr-vl convert https://example.com/spec.pdf

# 批量 — 一个目录的 PDF，每份生成各自的 .md 与媒体文件夹
paddleocr-vl convert ~/pdfs/ -o ~/out/

# 管道到你的编辑器
paddleocr-vl convert report.pdf --stdout | glow
```

## 工作原理

1. **提交** — 上传 PDF（或传入远程 URL），获取 `jobId`
2. **轮询** — 每 5 秒查询作业状态
3. **下载** — 获取包含 Markdown 文本与图片 URL 的 JSONL
4. **解析** — 组装 Markdown，并把图片下载到 `_media` 文件夹

## 文档

- [参考](docs/reference.md) — 全部 CLI 参数
- [特性与选项](docs/features.md) — 布尔开关、数值/字符串选项与优先级
- [安装](docs/install.md) — pip、本地 clone、`uv` 升级
- [故障排查](docs/troubleshooting.md) — 错误与静默失败

## 许可证

GNU General Public License v3.0 — 详见 [LICENSE](LICENSE)。
