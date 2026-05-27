# paddleocr-vl

使用 PaddleOCR-VL-1.5 百度官方 API 将 PDF 转换为 Markdown 的命令行工具。

## 安装

```bash
# 需要先设置 API token
export PADDLEOCR_API_TOKEN="your_token_here"

# 方式一：全局安装（推荐）
uv tool install /path/to/paddleocr-vl

# 方式二：直接运行
uv run python -m paddleocr_vl convert input.pdf
```

## 使用

### 单文件转换

```bash
# 输出到 PDF 同目录（input.md）
paddleocr-vl convert report.pdf

# 指定输出路径
paddleocr-vl convert report.pdf -o output/report.md

# 输出到 stdout（可管道到其他工具）
paddleocr-vl convert report.pdf --stdout | glow
```

### 批量转换

```bash
# 转换目录下所有 PDF
paddleocr-vl convert ~/pdfs/ -o ~/output/

# 使用默认输出目录（./output/）
paddleocr-vl convert ~/pdfs/
```

### 完整选项

```
paddleocr-vl convert <input> [options]

位置参数:
  input                 PDF 文件路径 或 包含 PDF 的目录

选项:
  -o, --output PATH     输出路径（文件或目录）
  --stdout              输出 Markdown 到 stdout
  --media-dir PATH      图片保存目录
  --token TEXT          API token（默认读取 $PADDLEOCR_API_TOKEN）
  --api-base-url URL    API 地址
  --model TEXT          模型名
  --timeout SECONDS     作业超时（默认 1800s）
  --poll-interval SEC   轮询间隔（默认 5s）
  --enable-all-features 不关闭可选特性
  --verbose, -v         详细日志
  --version, -V         显示版本
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `PADDLEOCR_API_TOKEN` | PaddleOCR API 访问令牌（必填） |
