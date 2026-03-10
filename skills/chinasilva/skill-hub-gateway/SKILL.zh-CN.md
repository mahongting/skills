# Skill Hub Gateway（简体中文）

默认 API 地址：`https://gateway-api.binaryworks.app`

英文文档：`SKILL.md`

## 版本检查协议（Agent）

- 官方最新版本来源：`GET /skills/manifest.json` 的 `data.version`。
- 本地当前版本来源：已安装 `SKILL.md` frontmatter 中的 `version`。
- 版本比较规则：使用语义化版本顺序（`major.minor.patch`）。
- 检查频率：会话启动时检查一次；同一会话内最多每 24 小时再检查一次。
- 检查失败（网络/超时/解析错误）时不得阻断运行时调用，继续当前流程并在下一次允许窗口重试。

## 更新决策流程（Agent）

- 当 `latest_version > current_version` 时，Agent 需读取本文档 `Release Notes` 对应版本小节生成 `update_summary`。
- Agent 需向用户展示：
  - `current_version`
  - `latest_version`
  - `update_summary`
- 用户决策选项：
  - `立即更新`
  - `本会话稍后提醒`
- 若用户选择 `本会话稍后提醒`，同一会话内针对同一目标版本不重复提示；新会话可再次提示。

## 首次接入（install_code）

脚本默认会自动完成接入流程：

1. 调用 `POST /agent/install-code/issue`，请求体可用 `{"channel":"local"}` 或 `{"channel":"clawhub"}`。
2. 读取 `data.install_code`。
3. 调用 `POST /agent/bootstrap`，请求体：`{"agent_uid":"<agent_uid>","install_code":"<install_code>"}`。
4. 读取 `data.api_key`，后续通过 `X-API-Key` 或 `Authorization: Bearer <api_key>` 调用。

手工覆盖方式：

- 仍可显式传入 `api_key`。
- 若未传 `agent_uid` 与 `owner_uid_hint`，脚本会基于当前工作目录生成稳定的本地默认值。

## 运行时协议（V2）

- 提交：`POST /skill/execute`
- 轮询：`GET /skill/runs/:run_id`
- 图片类能力统一使用 `image_url`，支持文件上传和 URL 两种模式；若使用 URL 模式，`image_url` 需为可直接下载图片的直链（返回头应为 `image/*`），不能是网页地址。
- 终态：`succeeded` / `failed`
- `succeeded` 返回 `output`
- `failed` 返回 `error.code`、`error.message`

## 输入来源说明

- 图片类能力（包括 `human_detect`、`image_tagging` 以及全部 Roboflow 图片能力）可直接上传图片，或显式传入 `image_url`。
- 随包 CLI 脚本（`scripts/execute.mjs` / `scripts/poll.mjs`）本身不提供上传参数；它们只会发送你传入的 JSON。
- 本 Skill 支持用户直接上传媒体/文档（含聊天附件）：
  - 使用 `image_url` 的图片类能力
  - `asr` 使用 `audio_url`
  - `markdown_convert` 使用 `file_url`
- 在执行前，系统内部可能会将上传文件归一化为临时对象 URL 再调用上游能力。
- 若调用方走显式 URL 模式，请提供可直接下载的 `image_url`、`audio_url` 或 `file_url`；本地文件路径和网页 URL 都不是有效输入。
- 当 bootstrap/execute/poll 失败时，请保留返回中的 `request_id`。脚本 stderr 现会输出 `status`、`code`、`message`、`request_id` 便于排障。

## 能力 ID

- `human_detect`
- `image_tagging`
- `tts_report`
- `embeddings`
- `reranker`
- `asr`
- `tts_low_cost`
- `markdown_convert`
- `face-detect`
- `person-detect`
- `hand-detect`
- `body-keypoints-2d`
- `body-contour-63pt`
- `face-keypoints-106pt`
- `head-pose`
- `face-feature-classification`
- `face-action-classification`
- `face-image-quality`
- `face-emotion-recognition`
- `face-physical-attributes`
- `face-social-attributes`
- `political-figure-recognition`
- `designated-person-recognition`
- `exhibit-image-recognition`
- `person-instance-segmentation`
- `person-semantic-segmentation`
- `concert-cutout`
- `full-body-matting`
- `head-matting`
- `product-cutout`

## 打包脚本参数

- `scripts/execute.mjs`：`[api_key] [capability] [input_json] [base_url] [agent_uid] [owner_uid_hint]`
- `scripts/poll.mjs`：`[api_key] <run_id> [base_url] [agent_uid] [owner_uid_hint]`
- `scripts/runtime-auth.mjs`：共享自动 bootstrap 逻辑

## Release Notes

发布新版本时请在此追加小节。Agent 面向用户展示的更新摘要必须基于本区块生成。

### 2.3.2（2026-03-10）

**What's New**

- 对齐能力参考文档与运行时口径：宿主侧可支持文件上传/聊天附件，运行时可能将上传文件归一化为 URL 再执行。
- 同步打包参考 `openapi` 版本与 `SKILL.md` frontmatter 版本，避免发布元数据漂移。
- 增加打包层测试护栏，提前阻断文档与版本不一致问题。

**Breaking/Behavior Changes**

- 无。

**Migration Notes**

- 现有运行时 API 调用方式不变。
- 若调用方会缓存 manifest 里的能力说明，请刷新缓存以获取澄清后的上传文案。

### 2.3.1（2026-03-10）

**What's New**

- 明确上传边界：CLI 脚本不负责上传，上传能力依赖宿主调用方链路。
- 为 CLI 脚本补充结构化失败日志（`status`、`code`、`message`、`request_id`），覆盖 bootstrap/execute/poll 排障场景。

**Breaking/Behavior Changes**

- 无。

**Migration Notes**

- 现有 API 调用方式不变。
- 若调用方会解析脚本 stderr，请兼容新增 JSON 错误日志事件。

### 2.3.0（2026-03-10）

**What's New**

- 新增基于 `/skills/manifest.json` 的 Agent 侧版本检查协议。
- 新增 Agent 更新确认决策流程（`立即更新` / `本会话稍后提醒`）。
- 明确 `Release Notes` 为用户更新内容摘要的唯一文档来源。

**Breaking/Behavior Changes**

- 无。

**Migration Notes**

- 现有运行时 API 调用方式无需变更。
- 如需启用更新提醒，Agent 实现需解析本区块并对比已安装版本与 `data.version`。
