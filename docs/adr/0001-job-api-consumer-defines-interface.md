# 0001: HTTP 接口由消费者定义

`JobApi` Protocol 住在 `src/paddleocr_vl/conversion.py`,由 `Conversion` 声明它需要什么;`src/paddleocr_vl/api.py` `import` 这个 Protocol 并提供 `RequestsJobApi` 实现。依赖方向是 `api → conversion`,不是反过来。

这是消费者驱动接口(consumer-defined interface)的应用:把"我需要什么"放在消费方,把"我提供什么"放在提供方。下次有人想把 Protocol 移到 `api.py` 时,这则 ADR 提醒他们那是反向依赖。
