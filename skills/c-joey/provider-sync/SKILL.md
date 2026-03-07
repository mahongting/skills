---
name: provider-sync
description: 从上游 provider 元数据接口或模型列表接口同步模型与相关参数到本地 OpenClaw 配置，支持 dry-run 预览、字段映射、模型能力规范化、Gemini 场景增强、模型级 diff 摘要、最小变更写入和备份回滚。用于需要安全同步 provider 配置、减少手工维护、批量更新模型列表，或在官方/第三方/Gemini 混合环境中复用同一套同步流程的场景。
---

# Provider Sync

执行目标：从上游接口获取 provider 信息，按映射规则生成最小配置变更，并安全写入本地 OpenClaw 配置。

## 工作方式

按以下顺序执行：

1. 读取目标配置文件（默认 `/root/.openclaw/openclaw.json`）。
2. 确认目标 provider 位于 `models.providers.<provider-id>`，默认只修改该 provider 子树。
3. 读取映射文件，将上游响应字段映射到本地配置路径。
4. 先执行 `dry-run` 或 `check-only`，输出变更摘要、模型摘要、模型级 diff、兼容模式探测结果。
5. 如需要将上游模型列表转成 OpenClaw 可用结构，启用 `--normalize-models`。
6. 如是 Gemini 场景，优先考虑 `--normalize-profile gemini`。
7. 如需保留本地已手工校准的模型能力字段，启用 `--preserve-existing-model-fields`。
8. 只有在用户明确确认后才执行真实写入；写入前自动生成带时间戳的备份。
9. 如需把变更应用到运行中的 OpenClaw，再单独走配置验证、应用或重启流程。

## 默认原则

- 默认优先 **dry-run → 用户确认 → apply**。
- 默认优先 **最小变更写入**，不要改无关字段。
- 默认优先 **保留本地手写能力字段**，避免覆盖人工校准结果。
- 默认不要跨出目标 provider 子树；只有明确需要时才允许额外路径写入。
- 如检测多个 API 兼容模式，给出推荐值，不要假定唯一正确答案。
- 对第三方和 Gemini 场景，优先强调“mapping + normalization profile”的适配方式，不要假装自动理解一切上游接口。

## 主脚本

使用脚本：`scripts/provider_sync.py`

常见调用：

```bash
python3 scripts/provider_sync.py \
  --provider-id cliplus \
  --endpoint https://api.example.com/provider/meta \
  --mapping-file references/mapping.example.json \
  --normalize-models \
  --preserve-existing-model-fields \
  --probe-api-modes openai-responses,openai-completions \
  --dry-run
```

确认后去掉 `--dry-run` 执行真实写入。

## 何时读取附加参考资料

- 需要接入新的上游接口模式时，读取 `references/provider-patterns.md`
- 需要理解模型字段如何规范化时，读取 `references/field-normalization.md`
- 需要接入 Gemini 官方接口或 Gemini 第三方代理时，读取 `references/gemini.md`
- 需要确认安全边界、备份和回滚策略时，读取 `references/safety-rules.md`
- 需要快速套用命令模板时，读取 `references/examples.md`
- 需要编写映射规则时，参考 `references/mapping.example.json`

## 主脚本支持的关键参数

- `--include-model` / `--exclude-model`：按模型 id 过滤同步范围
- `--check-only`：只校验拉取、映射、探测流程，不写入文件
- `--output json`：输出结构化摘要，便于自动化或二次处理
- `--normalize-profile gemini`：对 Gemini 场景使用更合适的字段推断
- `--preserve-existing-model-fields`：尽量保留本地已校准的模型能力字段

## 输出要求

优先给出简洁摘要，至少覆盖：

- 变更了哪些路径
- 模型数量变化
- 每个模型的关键能力（input / reasoning / contextWindow / maxTokens）
- 是否探测到可用 API 模式
- 模型差异摘要（added / removed / kept / changed）
- 关键字段前后值摘要
- 是否仅为 dry-run / check-only
- 如执行真实写入，备份文件路径是什么

如在 Telegram / Discord 等对表格支持一般的环境，可用项目符号代替表格；核心是清晰，不是格式本身。

## 边界说明

- 它不是“自动理解所有 provider 的万能工具”。
- 它不是整个 OpenClaw 配置系统的完整替代品。
- 它的通用性来自 **mapping + normalization profile**，不是黑盒自动识别一切。

## 安全约束

- 不在日志中输出完整密钥、Token、Authorization 值。
- 任何真实写入前都必须先做 dry-run 或明确说明将写入什么。
- 默认仅改动 `models.providers.<provider-id>`；跨域写入需显式开启。
- 写入失败时保留备份并回报原始错误。
- 如变更会影响运行中的 OpenClaw，不要假设热更新成功；应提示用户单独验证并决定是否应用。
