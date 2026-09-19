# 开发状态

更新时间：2026-09-19

## 已完成

- 完成产品规划和 AI 开发方案。
- 创建 Vue 3 + TypeScript + Vite 前端工作台骨架，包含项目列表、八步流程导航、输入页、规划页、占位步骤页和任务动态面板。
- 创建 FastAPI 本地开发后端，包含用户、项目、任务表，项目归属检查和任务状态接口。
- 完成关键词/脚本项目创建、项目保存、规划任务提交和后台进度轮询。
- `plan` 任务完成后写入可编辑的故事一句话、章节和旁白草稿。
- `render` 任务调用本机 FFmpeg 输出真实 1280x720、4 秒 MP4；预览接口以 `video/mp4` 返回。
- 增加 OpenAI 兼容文本渠道适配器：未配置时使用显式 local-demo，配置 `HBG_TEXT_API_BASE/KEY/MODEL` 后对规划结果做 JSON 结构校验；密钥不写入项目。
- 增加前端/后端 Dockerfile、Compose 起步配置和本地运行文档。
- 取消接口现在会取消进程内任务句柄，并防止迟到的协程结果覆盖 `cancelled` 状态。
- 工作台已增加可编辑人物锚点和分镜提示词页面；`storyboard` 任务会保存 4 个结构化镜头，`narration/images` 会保存演示结果元数据。
- 增加可独立启动的本地持久 Worker；`HBG_TASK_MODE=worker` 时 API 只落库排队，Worker 领取后执行。已用独立本地 SQLite 和 8001 端口完成 storyboard 队列验收。

## 验证证据

- `apps/web`: `npm run build` 通过，Vue 类型检查和 Vite 生产构建均通过。
- `backend`: `python -m compileall -q app` 通过。
- 本机 `127.0.0.1:8000/api/health` 返回 `status=ok`、`mode=local-demo`。
- 创建项目后提交 `plan`，任务从 queued/running 进入 succeeded，并保存故事结构。
- 提交 `render` 后用 FFprobe 检查得到 H.264、1280x720、4.0 秒、9584 字节 MP4；预览接口返回 `content-type=video/mp4`。

## 当前明确限制

- 登录目前是本地演示会话 `demo-user`，尚未接入正式密码/OAuth/JWT。
- 默认本地开发仍使用进程内 asyncio；Compose 已提供独立 Worker 配置。Celery/Redis、租约超时和异常重启重试尚未完成。
- `storyboard/narration/images` 当前是本地演示任务，尚未调用真实图片或语音供应商；`plan` 已支持可选 OpenAI 兼容文本渠道。
- `render` 当前先输出可验证的 FFmpeg 片头卡片，还没有把 HBG 现有脚本接入真实素材时间轴。
- 项目数据使用本机 SQLite；生产 PostgreSQL、对象存储、额度流水、管理员后台尚未完成。

## 下一阶段

1. 为脚本、人物、分镜和素材增加正式版本表与并发冲突检查。
2. 接入 Celery/Redis 或等价的租约/重试机制，补齐 Worker 重启恢复和幂等调用。
3. 封装现有 `build_script.mjs`、`build_narration.mjs`、`render_streaming_ffmpeg.mjs`，实现真实旁白、字幕和素材渲染。
4. 接入由用户提供的图片和语音渠道，先做单次真实小样再开放批量。
