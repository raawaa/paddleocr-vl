# 0003: Config 配置文件仅持久化布尔 feature flag

`src/paddleocr_vl/config.py` 的 `FEATURE_MAP` 只列出 11 个布尔 flag 与 API key 的映射，`read_features()` 也只返回这一段。`cli.py:build_optional_payload` 的合并路径只覆盖 `payload.update(config_features)` 这一段，再叠加 `--enable-all-features` 与单 flag。数值 Option（temperature、top-p、repetition-penalty、layout-threshold、layout-unclip-ratio、min-pixels、max-pixels）与字符串 Option（layout-merge-bboxes-mode、layout-shape-mode、prompt-label）**永远不写入** `~/.config/paddleocr-vl/config.json`。

为什么只持久化布尔：feature flag 是"开关——一开全开"的语义，适合持久化为跨次调用的偏好；数值与字符串 Option 是"按次生效"的语义——采样温度、版面阈值、提示标签都是按当前 PDF 调的，应当显式传。下次有人想把 `--temperature` 加进 `config set` 时，这则 ADR 提醒他们这与"boolean toggle"是反向语义。

代价：用户想在多份 PDF 上复用同一组调参，得用 shell alias 或 wrapper 脚本，不在 config 文件里沉淀。
