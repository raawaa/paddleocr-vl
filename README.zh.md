# paddleocr-vl

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)

[English](README.md) | [中文](README.zh.md)

使用 [PaddleOCR-VL-1.6](https://github.com/PaddlePaddle/PaddleOCR) 百度 API 将 PDF 转换为 Markdown 的 CLI 工具。

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

# 从远程 URL 转换 PDF
paddleocr-vl convert https://example.com/document.pdf

# 开启可选特性
paddleocr-vl convert input.pdf --chart-recognition
paddleocr-vl convert input.pdf --enable-all-features --no-doc-unwarping

# 调整模型推理参数
paddleocr-vl convert input.pdf --temperature 0.3 --top-p 0.9

# 跨页表格合并 + 标题层级重构
paddleocr-vl convert input.pdf --restructure-pages

# 关闭版面检测，仅做纯 OCR
paddleocr-vl convert input.pdf --no-layout-detection

# 指定版面模型参数
paddleocr-vl convert input.pdf --layout-threshold 0.3 --layout-nms
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

PaddleOCR-VL-1.6 API 提供丰富的可选参数，按类型分为三类：

#### 布尔开关特性

默认**全部关闭**以节省处理时间和费用：

| 特性 | 参数 | 说明 |
|------|------|------|
| 文档方向分类 | `--orientation-classify` | 自动检测并纠正页面方向 |
| 文档扭曲矫正 | `--doc-unwarping` | 矫正弯曲或倾斜的文档照片 |
| 图表识别 | `--chart-recognition` | 提取并结构化图表内容 |
| 版面检测 | `--layout-detection` | 自动检测文档中不同区域并排序 |
| 去除重叠框 | `--layout-nms` | 移除重复或高度重叠的区域框 |
| Markdown 美化 | `--prettify-markdown` | 输出格式化 Markdown 文本 |
| 公式编号 | `--show-formula-number` | 在输出中显示公式编号 |
| 可视化输出 | `--visualize` | 返回可视化中间图像 |
| 页面重构 | `--restructure-pages` | 多页 PDF 跨页表格合并+标题层级识别 |
| 跨页表格 | `--merge-tables` | 识别并合并跨页表格 |
| 标题识别 | `--relevel-titles` | 识别段落标题级别 |

使用独立参数开启指定特性，或用 `--enable-all-features` 一次开启全部布尔特性。

如需持久化配置（每次转换自动生效）：

```bash
paddleocr-vl config enable-feature layout-detection
paddleocr-vl config disable-feature chart-recognition
```

#### 数值参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `--temperature` | float | 采样温度，结果不稳定时调低 |
| `--top-p` | float | Top-p 采样，结果发散时调低 |
| `--repetition-penalty` | float | 重复惩罚系数，出现重复内容时调高 |
| `--layout-threshold` | float | 版面模型得分阈值（0-1，默认 0.5） |
| `--layout-unclip-ratio` | float | 检测框扩展系数（默认 1.0） |
| `--min-pixels` | int | 输入图片最小像素值 |
| `--max-pixels` | int | 输入图片最大像素值 |

#### 字符串参数

| 参数 | 可选值 | 说明 |
|------|--------|------|
| `--layout-merge-bboxes-mode` | `large`, `small`, `union` | 框合并模式 |
| `--layout-shape-mode` | `rect`, `quad`, `poly`, `auto` | 几何形状 |
| `--prompt-label` | `ocr`, `formula`, `table`, `chart` | 提示标签（关闭版面检测时生效） |

#### 参数优先级

多来源冲突时，按以下顺序决定最终值（后者覆盖前者）：

1. 默认值 — 原有 3 个 Feature 默认 false
2. 配置文件 — 持久化偏好（仅布尔特性）
3. `--enable-all-features` — 开启所有布尔特性
4. 独立 CLI 参数 — 显式覆盖

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
usage: paddleocr-vl convert [-h] [-o OUTPUT] [--stdout] [--media-dir MEDIA_DIR]
                            [--token TOKEN] [--api-base-url API_BASE_URL]
                            [--model MODEL] [--timeout TIMEOUT]
                            [--poll-interval POLL_INTERVAL]
                            [--enable-all-features]
                            [--orientation-classify | --no-orientation-classify]
                            [--doc-unwarping | --no-doc-unwarping]
                            [--chart-recognition | --no-chart-recognition]
                            [--layout-detection | --no-layout-detection]
                            [--layout-nms | --no-layout-nms]
                            [--prettify-markdown | --no-prettify-markdown]
                            [--show-formula-number | --no-show-formula-number]
                            [--visualize | --no-visualize]
                            [--restructure-pages | --no-restructure-pages]
                            [--merge-tables | --no-merge-tables]
                            [--relevel-titles | --no-relevel-titles]
                            [--temperature TEMPERATURE] [--top-p TOP_P]
                            [--repetition-penalty REPETITION_PENALTY]
                            [--layout-threshold LAYOUT_THRESHOLD]
                            [--layout-unclip-ratio LAYOUT_UNCLIP_RATIO]
                            [--min-pixels MIN_PIXELS]
                            [--max-pixels MAX_PIXELS]
                            [--layout-merge-bboxes-mode {large,small,union}]
                            [--layout-shape-mode {rect,quad,poly,auto}]
                            [--prompt-label {ocr,formula,table,chart}]
                            [--verbose] input

positional arguments:
  input                  PDF 文件路径、URL 或包含 PDF 的目录

options:
  -h, --help             show this help message and exit
  -o, --output OUTPUT    输出路径（文件或目录）
  --stdout               输出 Markdown 到 stdout
  --media-dir MEDIA_DIR  图片保存目录
  --token TOKEN          API token（默认读取配置文件或 $PADDLEOCR_API_TOKEN）
  --api-base-url URL     API 地址（默认: https://paddleocr.aistudio-app.com/api/v2/ocr/jobs）
  --model MODEL          模型名（默认: PaddleOCR-VL-1.6）
  --timeout TIMEOUT      作业超时秒数（默认: 1800）
  --poll-interval SEC    轮询间隔秒数（默认: 5）
  --enable-all-features  开启所有可选特性
  --orientation-classify, --no-orientation-classify   开启/关闭文档方向分类
  --doc-unwarping, --no-doc-unwarping                 开启/关闭文档扭曲矫正
  --chart-recognition, --no-chart-recognition         开启/关闭图表识别
  --layout-detection, --no-layout-detection           启用/关闭版面检测
  --layout-nms, --no-layout-nms                       移除重复或高度重叠的区域框
  --prettify-markdown, --no-prettify-markdown         Markdown 美化输出
  --show-formula-number, --no-show-formula-number     显示公式编号
  --visualize, --no-visualize                         返回可视化中间图
  --restructure-pages, --no-restructure-pages         对多页 PDF 进行重构
  --merge-tables, --no-merge-tables                   跨页表格合并
  --relevel-titles, --no-relevel-titles               段落标题级别识别
  --temperature TEMPERATURE                           采样温度
  --top-p TOP_P                                       Top-p 采样
  --repetition-penalty REPETITION_PENALTY             重复惩罚系数
  --layout-threshold LAYOUT_THRESHOLD                 版面模型得分阈值
  --layout-unclip-ratio LAYOUT_UNCLIP_RATIO           检测框扩展系数
  --min-pixels MIN_PIXELS                             输入图片最小像素值
  --max-pixels MAX_PIXELS                             输入图片最大像素值
  --layout-merge-bboxes-mode {large,small,union}      框合并模式
  --layout-shape-mode {rect,quad,poly,auto}           几何形状
  --prompt-label {ocr,formula,table,chart}            提示标签
  --verbose, -v                                       详细日志
```

## 工作原理

PaddleOCR API 使用**异步任务**模型：

1. **提交** — 上传 PDF 文件（或传入远程 PDF URL）到 API 接口，获取 `jobId`
2. **轮询** — 每 5 秒查询任务状态，直到处理完成
3. **下载** — 获取包含 Markdown 文本和图片 URL 的 JSONL 结果
4. **解析** — 提取 Markdown 内容并在本地下载嵌入的图片

## 许可证

本项目基于 GNU General Public License v3.0 开源 — 详见 [LICENSE](LICENSE) 文件。
