# paddleocr-vl

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

[English](README.md) | [中文](README.zh.md)

使用 [PaddleOCR-VL-1.5](https://github.com/PaddlePaddle/PaddleOCR) 百度 API 将 PDF 转换为 Markdown 的 CLI 工具。

## 快速开始

```bash
# 1. 安装
uv tool install git+https://github.com/raawaa/paddleocr-vl.git

# 2. 设置 API token（一次性）
paddleocr-vl config set-token "你的_token"

# 3. 转换 PDF
paddleocr-vl convert report.pdf
```

完成。Markdown 文件将生成在 `report.md`。

> **环境要求：** Python 3.10+ 和 [PaddleOCR API token](https://aistudio.baidu.com/paddleocr)。

### 其他安装方式

```bash
# 通过 pip 安装
pip install git+https://github.com/raawaa/paddleocr-vl.git

# 或本地运行（不安装）
git clone https://github.com/raawaa/paddleocr-vl.git
cd paddleocr-vl
uv sync
uv run -m paddleocr_vl convert input.pdf
```

## 使用示例

```bash
# 转换单个 PDF（输出：input.pdf → input.md）
paddleocr-vl convert input.pdf

# 指定输出路径
paddleocr-vl convert input.pdf -o output/report.md

# 输出 Markdown 到 stdout（可管道到其他工具，如 glow）
paddleocr-vl convert input.pdf --stdout | glow

# 批量转换目录下的所有 PDF
paddleocr-vl convert ~/pdfs/ -o ~/output/

# 开启可选特性
paddleocr-vl convert input.pdf --chart-recognition
paddleocr-vl convert input.pdf --enable-all-features --no-doc-unwarping
```

## 配置

### API token

Token 按以下顺序解析（优先使用排在前面的）：

1. `--token` CLI 参数
2. `PADDLEOCR_API_TOKEN` 环境变量
3. 配置文件（Linux/macOS：`~/.config/paddleocr-vl/config.json`，Windows：`%APPDATA%\paddleocr-vl\config.json`）

```bash
# 方式 1：CLI 参数（单次覆盖）
paddleocr-vl convert input.pdf --token "你的_token"

# 方式 2：环境变量
export PADDLEOCR_API_TOKEN="你的_token"
paddleocr-vl convert input.pdf

# 方式 3：配置文件（设置一次，永久生效）
paddleocr-vl config set-token "你的_token"
paddleocr-vl convert input.pdf
```

### 可选特性

PaddleOCR-VL-1.5 API 提供三个可选处理特性，默认**全部关闭**以节省处理时间和费用：

| 特性 | 参数 | 说明 |
|------|------|------|
| 文档方向分类 | `--orientation-classify` | 自动检测并纠正页面方向 |
| 文档扭曲矫正 | `--doc-unwarping` | 矫正弯曲或倾斜的文档照片 |
| 图表识别 | `--chart-recognition` | 提取并结构化图表内容 |

使用独立参数开启指定特性，或用 `--enable-all-features` 一次开启全部。

如需持久化配置（每次转换自动生效）：

```bash
paddleocr-vl config enable-feature orientation-classify
paddleocr-vl config disable-feature orientation-classify
```

多来源冲突时，按以下顺序决定最终值（后者覆盖前者）：

1. 默认值 — 全部关闭
2. 配置文件 — 持久化偏好
3. `--enable-all-features` — 快速全开
4. 独立参数 — 显式覆盖

### 配置管理命令

```bash
paddleocr-vl config set-token "你的_token"   # 保存 token
paddleocr-vl config remove-token               # 删除 token
paddleocr-vl config enable-feature <名称>   # 开启特性
paddleocr-vl config disable-feature <名称>  # 关闭特性
paddleocr-vl config show                           # 查看当前配置
```

## 参考

```
paddleocr-vl convert <input> [options]

Positional arguments:
  input                 PDF 文件路径或包含 PDF 的目录

Options:
  -o, --output PATH             输出路径（文件或目录）
  --stdout                      输出 Markdown 到 stdout
  --media-dir PATH              图片保存目录
  --token TEXT                  API token
                                （默认：配置文件或 $PADDLEOCR_API_TOKEN）
  --api-base-url URL            API 地址
                                （默认：https://paddleocr.aistudio-app.com/api/v2/ocr/jobs）
  --model TEXT                  模型名（默认：PaddleOCR-VL-1.5）
  --timeout SECONDS             作业超时秒数（默认：1800）
  --poll-interval SEC           轮询间隔秒数（默认：5）
  --enable-all-features         开启所有可选特性
  --orientation-classify /      开启/关闭文档方向分类
  --no-orientation-classify
  --doc-unwarping /             开启/关闭文档扭曲矫正
  --no-doc-unwarping
  --chart-recognition /         开启/关闭图表识别
  --no-chart-recognition
  --verbose, -v                 详细日志
  --version, -V                 显示版本
```

## 工作原理

PaddleOCR API 使用**异步任务**模型：

1. **提交** — 上传 PDF 文件到 API 接口，获取 `jobId`
2. **轮询** — 每 5 秒查询任务状态，直到处理完成
3. **下载** — 获取包含 Markdown 文本和图片 URL 的 JSONL 结果
4. **解析** — 提取 Markdown 内容并在本地下载嵌入的图片

## 许可证

本项目基于 GNU General Public License v3.0 开源 — 详见 [LICENSE](LICENSE) 文件。
