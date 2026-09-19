# 开发状态

更新时间：2026-09-19

项目根目录：`ai_life_apply/`。当前基线提交：`e74e0d2`（本轮技术规划前的代码基线）。以下实现与历史验证分开记录；本轮未重新执行应用/数据库/真实渠道测试。

## 本轮技术规划

- 新增 [详细技术方案](./technical-design.md)、[数据模型](./data-model.md)、[API 契约](./api-contract.md)、[工作流设计](./workflow-design.md)。
- 新增 [验收矩阵](./acceptance.md)、[AI 开发工作包](./implementation-backlog.md) 和 [架构决策](./adr/README.md)。
- 修正旧规划和开发启动任务的根目录说明；所有网站工作都以 `ai_life_apply/` 为根目录。
- 方案中的 PostgreSQL、正式会话、版本、额度、Celery 和真实素材闭环仍为待实现；文档完成不等于这些功能通过验收。
- 本轮文档检查：17 份 Markdown、44 个本地文件链接、5 个 JSON 示例均通过；同时检查代码围栏和表格列数。应用测试和数据库测试未执行。

## 已完成

- 完成产品规划和 AI 开发方案。
- 创建 Vue 3 + TypeScript + Vite 前端工作台骨架，包含项目列表、八步流程导航、输入页、规划页、占位步骤页和任务动态面板。
- 创建 FastAPI 本地开发后端，包含用户、项目、任务表，项目归属检查和任务状态接口。
- 完成关键词/脚本项目创建、项目保存、规划任务提交和后台进度轮询。
- `plan` 任务完成后写入可编辑的故事一句话、章节和旁白草稿。
- `render` 任务调用本机 FFmpeg 输出真实 1280x720、4 秒 MP4；预览接口以 `video/mp4` 返回。
- 增加 OpenAI 兼容文本渠道适配器：未配置时使用显式 local-demo，配置 `HBG_TEXT_API_BASE/KEY/MODEL` 后对规划结果做 JSON 结构校验；密钥不写入项目。
- 增加前端/后端 Dockerfile、Compose 起步配置和本地运行文档。
- 取消接口会取消同进程 asyncio 任务句柄，并在演示进度循环中检查取消状态；不保证终止 `to_thread` 中的外部调用/FFmpeg，也不保证独立 Worker 的迟到写回，需按新工作流协议完善。
- 工作台已增加可编辑人物锚点和分镜提示词页面；`storyboard` 任务会保存 4 个结构化镜头，`narration/images` 会保存演示结果元数据。
- 增加可独立启动的本地持久 Worker；`HBG_TASK_MODE=worker` 时 API 只落库排队，Worker 领取后执行。已用独立本地 SQLite 和 8001 端口完成 storyboard 队列验收。

## 历史验证证据（本轮未重跑）

- `apps/web`: `npm run build` 通过，Vue 类型检查和 Vite 生产构建均通过。
- `backend`: `python -m compileall -q app` 通过。
- 本机 `127.0.0.1:8000/api/health` 返回 `status=ok`、`mode=local-demo`。
- 创建项目后提交 `plan`，任务从 queued/running 进入 succeeded，并保存故事结构。
- 提交 `render` 后用 FFprobe 检查得到 H.264、1280x720、4.0 秒、9584 字节 MP4；预览接口返回 `content-type=video/mp4`。

## 当前明确限制

- 登录目前是本地演示会话 `demo-user`，尚未接入正式密码认证和可撤销的服务端会话。
- 默认本地开发仍使用进程内 asyncio；Compose 已提供独立 Worker 配置。Celery/Redis、租约超时和异常重启重试尚未完成。
- `storyboard/narration/images` 当前是本地演示任务，尚未调用真实图片或语音供应商；`plan` 已支持可选 OpenAI 兼容文本渠道。
- `render` 当前先输出可验证的 FFmpeg 片头卡片，还没有把 HBG 现有脚本接入真实素材时间轴。
- 项目数据使用本机 SQLite；生产 PostgreSQL、对象存储、额度流水、管理员后台尚未完成。
- 配置真实文本渠道目前只生成大纲，旁白正文仍是固定演示稿；真实写稿流程待 M3 完成。
- 网站部署缺少同源 API 代理，前端默认地址仍为 `127.0.0.1:8000`；现有 CI 主要检查制作脚本，尚未覆盖完整应用。

## 下一阶段

1. 按 M1 补齐配置/同源 API、本机迁移、正式会话与私人空间、脚本和项目版本。
2. 按 M2 建立私有资产、持久任务与事件、幂等和额度，打通带图片/旁白/字幕的本地夹具视频。
3. 按 M3–M5 提前验证真实文本/图片/语音小样，完善人物场景、分镜与批量局部恢复。
4. 按 M6–M8 完成八步工作台、真实合成、管理员和故障验收、部署恢复演练。具体边界见 implementation-backlog。
