import argparse
import itertools
import sys
import time
from pathlib import Path

from . import __version__
from . import config as _config
from .api import (
    API_BASE_URL,
    API_MODEL,
    DEFAULT_OPTIONAL_PAYLOAD,
    JOB_TIMEOUT,
    POLL_INTERVAL,
    download_result,
    poll_job,
    read_api_token,
    submit_job,
)
from .errors import JobTimeoutError, PaddleOCRError, RateLimitError
from .parser import parse_jsonl_to_markdown


# CLI 短名到 API payload key 的映射
CLI_FEATURE_FLAGS = {
    "orientation_classify": "useDocOrientationClassify",
    "doc_unwarping": "useDocUnwarping",
    "chart_recognition": "useChartRecognition",
}


class _Spinner:
    """简单的 CLI spinner，用 stdlib 实现。"""

    def __init__(self, msg="等待 OCR 作业完成"):
        self.msg = msg
        self._spinner = itertools.cycle(r"-\|/")
        self._running = False

    def __enter__(self):
        self._running = True
        return self

    def __exit__(self, *args):
        self._running = False
        sys.stderr.write("\r" + " " * 60 + "\r")
        sys.stderr.flush()

    def tick(self, elapsed: int):
        if not self._running:
            return
        sys.stderr.write(
            f"\r  {next(self._spinner)} {self.msg} ({elapsed}s)"
        )
        sys.stderr.flush()

    def done(self, elapsed: int):
        sys.stderr.write(f"\r  ✓ {self.msg}完成 ({elapsed}s)\n")
        sys.stderr.flush()


def detect_input_type(path_str: str) -> str:
    """判断输入是 pdf 文件、目录、还是无效。"""
    p = Path(path_str)
    if not p.exists():
        return "invalid"
    if p.is_file():
        return "pdf" if p.suffix.lower() == ".pdf" else "invalid"
    if p.is_dir():
        return "directory"
    return "invalid"


def is_real_pdf(path: Path) -> bool:
    if path.suffix.lower() != ".pdf":
        return False
    try:
        with open(path, "rb") as f:
            return f.read(5) == b"%PDF-"
    except Exception:
        return False


def collect_pdfs(directory: Path) -> list[Path]:
    """扫描目录下所有 PDF 文件。"""
    return sorted(
        p for p in directory.iterdir() if p.is_file() and is_real_pdf(p)
    )


def build_optional_payload(args) -> dict:
    """合并配置文件 + CLI flag，生成最终 optionalPayload。"""
    # 1. 硬编码默认值（全 False）
    payload = dict(DEFAULT_OPTIONAL_PAYLOAD)

    # 2. 配置文件覆盖
    config_features = _config.read_features()
    payload.update(config_features)

    # 3. --enable-all-features 覆盖
    if args.enable_all_features:
        for key in payload:
            payload[key] = True

    # 4. 独立 CLI flag 覆盖（仅当显式设置时）
    for attr, api_key in CLI_FEATURE_FLAGS.items():
        val = getattr(args, attr, None)
        if val is not None:
            payload[api_key] = val

    return payload


def convert_single(
    pdf_path: Path,
    api_token: str,
    *,
    output_path: Path | None = None,
    media_dir: Path | None = None,
    stdout: bool = False,
    verbose: bool = False,
    api_base_url: str = API_BASE_URL,
    model: str = API_MODEL,
    timeout: float = JOB_TIMEOUT,
    poll_interval: float = POLL_INTERVAL,
    optional_payload: dict | None = None,
) -> dict:
    """处理单个 PDF，返回结果字典。"""
    stem = pdf_path.stem
    pdf_size_mb = round(pdf_path.stat().st_size / 1024 / 1024, 2)

    # 确定媒体目录
    if media_dir is None:
        if output_path and output_path.is_dir():
            media_dir = output_path / stem
        elif output_path:
            media_dir = output_path.parent / f"{stem}_media"
        else:
            media_dir = pdf_path.parent / f"{stem}_media"

    t0 = time.time()

    job_id = submit_job(
        pdf_path,
        api_token,
        api_base_url=api_base_url,
        model=model,
        optional_payload=optional_payload,
    )

    if verbose:
        print(f"  job_id: {job_id}", file=sys.stderr)

    spinner = _Spinner()
    with spinner:
        result_data = poll_job(
            api_token,
            job_id,
            api_base_url=api_base_url,
            poll_interval=poll_interval,
            timeout=timeout,
            progress_callback=spinner.tick,
        )
    elapsed = time.time() - t0
    spinner.done(int(elapsed))

    jsonl_url = result_data.get("resultUrl", {}).get("jsonUrl", "")
    if not jsonl_url:
        raise RuntimeError("无法获取 jsonl 结果 URL")

    jsonl_text = download_result(jsonl_url)
    markdown_text = parse_jsonl_to_markdown(jsonl_text, media_dir, stem)

    if stdout:
        sys.stdout.write(markdown_text)
        if not markdown_text.endswith("\n"):
            sys.stdout.write("\n")
    else:
        if output_path:
            md_path = output_path
        else:
            md_path = pdf_path.with_suffix(".md")
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown_text, encoding="utf-8")

    elapsed_total = time.time() - t0
    return {
        "pdf": str(pdf_path),
        "pdf_size_mb": pdf_size_mb,
        "elapsed_s": round(elapsed_total, 2),
        "chars": len(markdown_text),
        "status": "ok",
    }


def convert_batch(
    pdf_dir: Path,
    api_token: str,
    *,
    output_dir: Path | None = None,
    verbose: bool = False,
    api_base_url: str = API_BASE_URL,
    model: str = API_MODEL,
    timeout: float = JOB_TIMEOUT,
    poll_interval: float = POLL_INTERVAL,
    optional_payload: dict | None = None,
) -> tuple[int, int]:
    """批量转换目录下所有 PDF。返回 (成功数, 失败数)。"""
    pdfs = collect_pdfs(pdf_dir)
    total = len(pdfs)

    if total == 0:
        print(f"目录中没有 PDF 文件: {pdf_dir}", file=sys.stderr)
        return 0, 0

    if output_dir is None:
        output_dir = Path("./output")
    output_dir.mkdir(parents=True, exist_ok=True)

    ok_count = 0
    fail_count = 0

    for i, pdf_path in enumerate(pdfs, 1):
        pdf_size_mb = round(pdf_path.stat().st_size / 1024 / 1024, 2)
        print(f"\n[{i}/{total}] {pdf_path.name} ({pdf_size_mb} MB)")

        try:
            result = convert_single(
                pdf_path,
                api_token,
                output_path=output_dir / f"{pdf_path.stem}.md",
                verbose=verbose,
                api_base_url=api_base_url,
                model=model,
                timeout=timeout,
                poll_interval=poll_interval,
                optional_payload=optional_payload,
            )
            ok_count += 1
            print(
                f"  ✓ {result['elapsed_s']:.1f}s | {result['chars']} 字符"
            )

        except RateLimitError as e:
            print(f"  限流: {str(e)[:100]}", file=sys.stderr)
            print(
                f"\n=== 批量处理中断: 已完成 {ok_count}/{total} ==="
            )
            return ok_count, fail_count + (total - i + 1)

        except PaddleOCRError as e:
            fail_count += 1
            print(f"  ✗ {str(e)[:100]}", file=sys.stderr)

        except Exception as e:
            fail_count += 1
            print(f"  ✗ {str(e)[:100]}", file=sys.stderr)

    return ok_count, fail_count


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="paddleocr-vl",
        description="使用 PaddleOCR-VL-1.5 API 将 PDF 转换为 Markdown",
    )
    parser.add_argument(
        "--version", "-V", action="version", version=f"paddleocr-vl {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    convert_parser = subparsers.add_parser(
        "convert", help="转换 PDF 为 Markdown"
    )
    convert_parser.add_argument(
        "input",
        help="PDF 文件路径 或 包含 PDF 的目录",
    )
    convert_parser.add_argument(
        "-o", "--output",
        help="输出路径（文件或目录）",
    )
    convert_parser.add_argument(
        "--stdout",
        action="store_true",
        help="输出 Markdown 到 stdout（仅单文件）",
    )
    convert_parser.add_argument(
        "--media-dir",
        help="图片保存目录",
    )
    convert_parser.add_argument(
        "--token",
        help="API token（默认读取配置文件或 $PADDLEOCR_API_TOKEN）",
    )
    convert_parser.add_argument(
        "--api-base-url",
        default=API_BASE_URL,
        help=f"API 地址（默认: {API_BASE_URL}）",
    )
    convert_parser.add_argument(
        "--model",
        default=API_MODEL,
        help=f"模型名（默认: {API_MODEL}）",
    )
    convert_parser.add_argument(
        "--timeout",
        type=float,
        default=JOB_TIMEOUT,
        help=f"作业超时秒数（默认: {JOB_TIMEOUT}）",
    )
    convert_parser.add_argument(
        "--poll-interval",
        type=float,
        default=POLL_INTERVAL,
        help=f"轮询间隔秒数（默认: {POLL_INTERVAL}）",
    )
    convert_parser.add_argument(
        "--enable-all-features",
        action="store_true",
        help="开启所有可选特性（文档方向分类/扭曲矫正/图表识别）",
    )
    convert_parser.add_argument(
        "--orientation-classify",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="开启文档方向分类",
    )
    convert_parser.add_argument(
        "--doc-unwarping",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="开启文档扭曲矫正",
    )
    convert_parser.add_argument(
        "--chart-recognition",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="开启图表识别",
    )
    convert_parser.add_argument(
        "--verbose", "-v", action="store_true", help="详细日志",
    )

    # config 子命令
    config_parser = subparsers.add_parser("config", help="管理配置")
    config_subparsers = config_parser.add_subparsers(dest="config_command", required=True)

    set_token_parser = config_subparsers.add_parser("set-token", help="设置 API token")
    set_token_parser.add_argument("token", help="API token")

    enable_feature_parser = config_subparsers.add_parser("enable-feature", help="开启可选特性（配置文件持久化）")
    enable_feature_parser.add_argument("name", help="特性名: orientation-classify / doc-unwarping / chart-recognition")

    disable_feature_parser = config_subparsers.add_parser("disable-feature", help="关闭可选特性（配置文件持久化）")
    disable_feature_parser.add_argument("name", help="特性名: orientation-classify / doc-unwarping / chart-recognition")

    remove_feature_parser = config_subparsers.add_parser("remove-feature", help="删除已保存的可选特性")
    remove_feature_parser.add_argument("name", help="特性名: orientation-classify / doc-unwarping / chart-recognition")

    config_subparsers.add_parser("show", help="查看当前配置")
    config_subparsers.add_parser("remove-token", help="删除 API token")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "config":
        if args.config_command == "set-token":
            _config.write_token(args.token)
            print(f"✓ Token 已保存到 {_config.get_config_path()}")
        elif args.config_command == "enable-feature":
            _config.set_feature(args.name, True)
            names = ", ".join(_config.FEATURE_MAP)
            print(f"✓ 特性 '{args.name}' 已开启")
            print(f"  可用特性: {names}")
        elif args.config_command == "disable-feature":
            _config.set_feature(args.name, False)
            names = ", ".join(_config.FEATURE_MAP)
            print(f"✓ 特性 '{args.name}' 已关闭")
            print(f"  可用特性: {names}")
        elif args.config_command == "remove-feature":
            _config.remove_feature(args.name)
            print(f"✓ 特性 '{args.name}' 已从配置中删除")
        elif args.config_command == "show":
            cfg = _config._read()
            token = cfg.get("api_token")
            if token:
                masked = token[:8] + "..." + token[-4:]
                print(f"API token: {masked}")
            else:
                print("API token: (未设置)")
            features = cfg.get("features", {})
            if features:
                print("可选特性:")
                for key, val in features.items():
                    status = "开启" if val else "关闭"
                    print(f"  {key}: {status}")
            else:
                print("可选特性: (未配置)")
            print(f"配置文件: {_config.get_config_path()}")
        elif args.config_command == "remove-token":
            _config.remove_token()
            print("✓ Token 已删除")
        return

    if args.command != "convert":
        parser.print_help()
        sys.exit(1)

    # 读取 token
    api_token = args.token or read_api_token()

    # 合并配置文件 + CLI flag 生成 optionalPayload
    optional_payload = build_optional_payload(args)

    # 判断输入类型
    input_type = detect_input_type(args.input)
    if input_type == "invalid":
        print(
            f"错误: 输入路径不存在或不是 PDF 文件/目录: {args.input}",
            file=sys.stderr,
        )
        sys.exit(1)

    # 单文件模式
    if input_type == "pdf":
        pdf_path = Path(args.input)

        if args.stdout and args.output:
            print(
                "错误: --stdout 和 -o 不能同时使用",
                file=sys.stderr,
            )
            sys.exit(1)

        if args.media_dir:
            media_path = Path(args.media_dir)
        else:
            media_path = None

        output_path = Path(args.output) if args.output else None

        try:
            result = convert_single(
                pdf_path,
                api_token,
                output_path=output_path,
                media_dir=media_path,
                stdout=args.stdout,
                verbose=args.verbose,
                api_base_url=args.api_base_url,
                model=args.model,
                timeout=args.timeout,
                poll_interval=args.poll_interval,
                optional_payload=optional_payload,
            )
            if not args.stdout:
                print(
                    f"✓ 完成: {result['elapsed_s']:.1f}s | "
                    f"{result['chars']} 字符"
                )
        except PaddleOCRError as e:
            print(f"错误: {e}", file=sys.stderr)
            sys.exit(1)

    # 目录批量模式
    else:
        if args.stdout:
            print(
                "错误: --stdout 不支持目录批量模式",
                file=sys.stderr,
            )
            sys.exit(1)

        if args.media_dir:
            print(
                "警告: --media-dir 在批量模式中会被忽略，"
                "图片将保存在各 PDF 输出目录中",
                file=sys.stderr,
            )

        output_dir = Path(args.output) if args.output else None

        ok_count, fail_count = convert_batch(
            Path(args.input),
            api_token,
            output_dir=output_dir,
            verbose=args.verbose,
            api_base_url=args.api_base_url,
            model=args.model,
            timeout=args.timeout,
            poll_interval=args.poll_interval,
            optional_payload=optional_payload,
        )
        total = ok_count + fail_count
        print(f"\n批量处理完成: {ok_count}/{total} 成功")
        if fail_count > 0:
            sys.exit(1)
