# 0002: 批量策略是 CLI 的责任

`Conversion` 一次只跑一个 source(单个 PDF 或单个 URL)。目录模式在 `src/paddleocr_vl/cli.py` 的 `main()` 里用循环处理,policy(限流中断整批、错误聚合继续)是 CLI 层的决策,不是 `Conversion` 的语义。

OO 直觉可能想造一个 `BatchConversion` 类来"集中"这些 policy;但 policy(尤其是"中断整批 vs 跳过这一项")是 CLI 进程关心的事,跟"PDF → markdown"的语义无关。这则 ADR 防止以后有人把批量循环搬进 `Conversion`。
