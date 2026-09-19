# API 契约 v1

日期：2026-09-19。状态：目标接口，尚未全部实现。当前 `/api/projects` 等演示接口见实际代码；不得把本文当作已可调用的接口清单。

## 1. 协议与统一规则

- 前缀 `/api/v1`；同源 HTTPS；JSON 字段统一 snake_case。旧 camelCase 响应在前端切换时统一转换，不长期同时保留两套领域类型。
- 会话用服务端 Cookie；状态变更验证 `X-CSRF-Token` 和 Origin。前端不在 localStorage 保存认证 token。
- UUID 作为实体 ID，时间 ISO 8601 UTC；时长字段带 `_ms`；容量 `_bytes`；积分整数 `_credits`。
- 成功 GET/PATCH 200、创建 201、长操作 202、删除/登出 204；单资源直接返回对象，列表返回 `items / next_cursor`。
- 列表 `limit=20`，最大 100，使用稳定排序和不透明游标；搜索只在当前空间范围执行。
- 修改可变资源要求 `If-Match: "v12"`，响应返回新 ETag。未提供 428，版本冲突 412。不可变内容修改创建新版本，再更新当前指针。
- 生成、导出、复制、额度调整需要 `Idempotency-Key`。同一用户/空间/路由/key 且请求摘要相同返回同一资源；摘要不同 409。终态至少保留 7 天，活跃操作不清理。
- 与目标引用相关的预算、权限、依赖检查全部在服务端执行。禁止用户自填任意 SQL、shell、回调 URL 或模型服务地址。

错误结构：

```json
{
  "error": {
    "code": "REVISION_CONFLICT",
    "message": "内容已更新，请比较最新版本后再保存。",
    "request_id": "request_example",
    "retryable": false,
    "details": { "expected_version": 12, "current_version": 13 }
  }
}
```

以下示例的易读 ID 为占位符，真实接口使用 UUID。

| HTTP | 错误码 | 前端处理 |
| --- | --- | --- |
| 401 | AUTH_REQUIRED / SESSION_EXPIRED | 保存当前编辑缓冲并转登录 |
| 403 | CSRF_INVALID / ACTION_FORBIDDEN | 停止自动重试，给出操作说明 |
| 404 | RESOURCE_NOT_FOUND | 包括不存在和不属于该空间的资源，避免泄露存在性 |
| 409 | IDEMPOTENCY_CONFLICT / DEPENDENCY_NOT_READY / QUOTE_STALE / BUDGET_EXCEEDED | 重新获取状态/报价，由用户选择继续 |
| 412 / 428 | REVISION_CONFLICT / PRECONDITION_REQUIRED | 比较版本或附带版本重新提交 |
| 413 / 415 / 422 | FILE_TOO_LARGE / MEDIA_UNSUPPORTED / VALIDATION_ERROR | 标出字段、文件或能力错误 |
| 429 | RATE_LIMITED | 尊重 Retry-After，保留输入 |
| 503 | PROVIDER_UNAVAILABLE / SERVICE_NOT_READY | 显示渠道/系统缺项，不显示模拟成功 |

## 2. 登录、邀请和管理账户

| 方法 | 路径 | 输入/返回 |
| --- | --- | --- |
| POST | `/auth/invitations/redeem` | invitation_token、email、password；创建账户、空间并签发会话 |
| POST | `/auth/sessions` | email/password；设置 Cookie，返回 user/workspace/csrf_token |
| DELETE | `/auth/session` | 撤销当前会话并清 Cookie，204 |
| GET | `/me` | 当前 user/workspace、permissions、csrf_token、运行模式 |
| POST | `/auth/password-resets/confirm` | 单次 token + 新密码，撤销旧会话 |
| POST | `/admin/invitations` | email、有效期；仅管理员；返回一次可复制邀请入口 |
| GET / PATCH | `/admin/users` / `/admin/users/{id}` | 分页账户元数据；启停账户，PATCH 要 ETag |
| POST | `/admin/users/{id}/password-resets` | 经管理员核实身份发起重置；单次链接，不回显原密码 |

登录和邀请兑换本身无已建立会话时，验证同源 Origin、JSON Content-Type、速率限制；不能以“没有 CSRF token”为理由允许任意来源创建/固定会话。错误信息不区分邮箱是否存在。

## 3. 项目、内容和版本接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET / POST | `/projects` | 列表或创建项目；POST 输入 title/input_mode/orientation/source_text/target_duration_ms/template_version_id |
| GET / PATCH | `/projects/{id}` | 项目简报和 UI 偏好；返回 lock_version，不允许任意覆盖 brief_json |
| POST | `/projects/{id}/copies` | 创建副本；显式说明复制结构/选用素材；新项目拥有独立预算与任务 |
| DELETE | `/projects/{id}` | 202，进入删除流程：取消任务→引用/保留策略→回收媒体 |
| GET | `/projects/{id}/workflow` | 八步状态、blockers、allowed_actions、当前生成/选用版本 |
| GET / POST | `/projects/{id}/sources` | 查看/导入原文；新版本不覆盖原始条目 |
| GET | `/projects/{id}/plans` | 分页规划候选；生成通过 runs 提交 |
| GET / POST | `/projects/{id}/scripts` | 查看版本/保存编辑稿；POST 指定 parent_version_id 与 project ETag |
| GET | `/projects/{id}/scripts/{version_id}/diff?base=...` | 当前空间两个脚本版本的差异 |
| POST | `/projects/{id}/revisions` | 按当前 lock_version 冻结不可变快照 |
| POST | `/projects/{id}/confirmations` | stage + project_revision_id，确认确定版本 |
| POST | `/projects/{id}/change-impact` | 只分析 proposed_changes 的下游影响/预估，不执行生成、不写正文 |
| GET / POST | `/characters`、`/scenes` | 当前空间素材库设定；POST 可带 origin_project_id |
| GET / PATCH | `/characters/{id}`、`/scenes/{id}` | 修改创建 version 并更新 current_version 指针 |
| GET | `/characters/{id}/versions`、`/scenes/{id}/versions` | 历史设定及参考图 |
| PUT | `/projects/{id}/characters/{character_id}`、`/projects/{id}/scenes/{scene_id}` | 项目引用明确 version_id；不自动跟随库最新版本 |
| GET / POST | `/projects/{id}/shots` | 镜头列表/手工增加 |
| PATCH | `/projects/{id}/shots/{shot_id}` | 内容/运动/引用编辑，产生新 shot_version |
| POST | `/projects/{id}/shots/{shot_id}/splits` | 指定文本边界拆镜头；原镜头归档，新 ID 创建 |
| POST | `/projects/{id}/shot-merges` | 同项目相邻 shot_ids 合并，保留原版本 |
| GET / POST | `/projects/{id}/shots/{shot_id}/prompts` | 查看/编辑提示词；保留语义描述和供应商参数 |
| GET | `/projects/{id}/shots/{shot_id}/candidates` | 候选、来源、引用版本和选用状态 |
| PUT | `/projects/{id}/shots/{shot_id}/selection` | asset_id + candidate_id + If-Match；验证归属和质量 |
| GET | `/projects/{id}/narrations` | 正式旁白版本、真实时长、音色、对齐状态 |
| GET / POST | `/projects/{id}/captions` | 查看/编辑字幕，引用 narration_version_id；影响朗读文本时提示重生成 |
| GET / POST | `/projects/{id}/timelines` | 时间轴/混音版本；引用明确素材、镜头、字幕 |

统一在资源事务内检查嵌套路径父子关系，不允许把 A 项目的 shot_id 放到 B 路径操作。分页镜头不返回图片 base64，返回 asset_id 和缩略图访问入口。

## 4. 报价和生成

`POST /projects/{id}/quotes` 输入如下，返回明细、报价时效、最大可结算积分、依赖检查：

```json
{
  "kind": "shot_images",
  "project_revision_id": "rev_example",
  "selection": { "shot_version_ids": ["shot_version_example"] },
  "parameters": { "candidates_per_shot": 1, "provider_config_version_id": "provider_example" }
}
```

`POST /projects/{id}/runs`，请求头有 `Idempotency-Key`，正文：

```json
{
  "kind": "shot_images",
  "project_revision_id": "rev_example",
  "quote_id": "quote_example",
  "budget_limit_credits": 20,
  "selection": { "shot_version_ids": ["shot_version_example"] },
  "parameters": { "candidates_per_shot": 1, "provider_config_version_id": "provider_example" }
}
```

积分 20 为示例，不代表实际价格。parameters 必须匹配报价摘要。返回 `202 Accepted` 和 `Location: /api/v1/runs/run_example`：

```json
{
  "id": "run_example",
  "project_id": "project_example",
  "project_revision_id": "rev_example",
  "kind": "shot_images",
  "status": "queued",
  "mode": "real",
  "progress": { "completed_items": 0, "total_items": 1 },
  "reserved_credits": 20,
  "created_at": "2026-09-19T08:00:00Z"
}
```

kind 枚举：`plan / script_rewrite / entities / character_reference / scene_reference / narration_sample / narration / storyboard / prompts / shot_images`。对每种 kind 使用独立 Pydantic discriminated union，拒绝未声明参数；批量数量、正文长度、候选数和输出尺寸有服务端上限。

preview/export 通过专属 exports 资源创建，内部仍产生 run；无需给前端暴露自定义 DAG。

报价接口允许上述生成 kind 及 `preview / final_export`，导出报价还绑定 timeline_version_id 和 profile；创建 exports 必须提交匹配报价。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/runs?project_id=&status=&cursor=` | 当前空间任务中心 |
| GET | `/runs/{id}` | 任务摘要、子项计数、取消/重试可用性 |
| GET | `/runs/{id}/nodes` | 分镜级进度、错误码、对应产物 |
| POST | `/runs/{id}/cancellations` | 202 或已终态 200；幂等取消意图 |
| POST | `/runs/{id}/retries` | 新 run，列出 failed node_ids、报价与预算；unknown 不允许盲重试 |
| GET | `/runs/{id}/events?after=` | 有界历史事件分页；SSE 异常时补查 |
| POST | `/admin/provider-requests/{id}/reconciliations` | 管理员提供核对证据或触发安全状态查询；写审计，不强行伪造成功 |

`GET /provider-capabilities?kind=` 只返回可选模型、音色/参考图/画幅能力、启用状态及用户可见的计量规则；不返回 endpoint、secret_ref 或真实密钥。

## 5. 上传、素材和下载

1. `POST /uploads`：指定 project_id 可空、kind、filename、size_bytes、mime_type。返回 upload_id、服务端指定上传方法/URL/限制/过期时间。
2. 本地存储模式 `PUT /uploads/{id}/content` 接受二进制流，要求会话和 CSRF；对象存储模式使用限 key/大小的签名上传并配置允许来源。
3. `POST /uploads/{id}/completions`：服务端按 staging_key 取实际文件，检查大小、hash、媒体解码，产生或返回同一 asset_id。客户端声明成功不能直接把 asset 标为 ready。
4. 检测完成才允许引用；失败文件保持隔离并按 TTL 清理。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/assets?project_id=&kind=&cursor=` | 私有素材库与来源/版本摘要 |
| GET | `/assets/{id}` | 尺寸、时长、质量和关联候选 |
| GET | `/assets/{id}/content` | Cookie 鉴权，视频/音频支持 Range 与 206；私有缓存策略 |
| POST | `/assets/{id}/download-tickets` | 短时下载凭证/URL；签发需鉴权，默认建议 5 分钟有效 |
| DELETE | `/assets/{id}` | 无引用则进入删除，存在当前/历史受保护引用则 409 并列影响 |

文件名仅用于下载显示；object_key 不由 filename 拼接。完成上传只能访问该 upload_session 的 key，禁止传另一个人的对象地址来认领文件。现有 preview 接口按项目共享路径会被 exports/asset 版本接口取代。

## 6. 导出和质量报告

`POST /projects/{id}/exports`：project_revision_id、timeline_version_id、profile=preview/final、quote_id、budget_limit_credits；带幂等键，返回 202、export_id、run_id。前置依赖必须齐全，不能以自动生成缺图作为导出的隐含费用。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/projects/{id}/exports` | 历史预览/正式版本 |
| GET | `/exports/{id}` | queued/rendering/checking/ready/failed/cancelled、媒体和 QA 引用 |
| GET | `/exports/{id}/qa` | 每项检测状态、工具版本、问题时间点和建议 |
| GET | `/exports/{id}/download?kind=video` | kind 可选 video、srt、vtt、cover；重新鉴权后受控下载或短时重定向，ready 才交付视频 |

不同 export_id 可以同时对应同一 timeline，产物不覆盖；修改草稿不会改变历史 export 的下载内容。用户若接受创作性黑场警告需记录解释，工具 error 和解码失败不提供“忽略继续”开关。

## 7. 额度和模型后台

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/usage/balance` | available/reserved/spent、配额和活跃任务数 |
| GET | `/usage/ledger?project_id=&cursor=` | 用户积分流水，分页；供应商成本默认不向普通用户披露 |
| POST | `/admin/workspaces/{id}/credit-adjustments` | amount、reason、幂等键；原子记账与审计 |
| GET | `/admin/provider-configs` | 渠道配置摘要及能力 |
| POST / PATCH | `/admin/provider-configs` / `/{id}` | 创建/更新配置版本，秘密引用独立处理 |
| POST | `/admin/provider-configs/{id}/checks` | 明确声明诊断类型；默认无付费调用；付费小样走独立报价/预算 |
| GET | `/admin/operations` | 队列、unknown、lease 超时、成本对账等聚合 |

渠道禁用阻止新提交，在途任务继续记录/核对，不能删除其配置版本或费用关联。密钥不在 GET 响应回显，日志对相关输入字段统一脱敏。

## 8. SSE 契约

`GET /events?after={seq}` 为当前空间一条事件流，`Content-Type: text/event-stream`。首次加载先取 REST 快照和 watermark，再从该 watermark 订阅。自动重连读取 `Last-Event-ID`；服务端以 header 优先于 query。归属从会话确定。

`GET /workspace-snapshot?project_id=` 返回当前账户余额、近期任务摘要、指定项目步骤/版本摘要和 event_watermark；范围有界，不打包全部媒体或脚本历史。快照中的所有摘要与 watermark 在同一一致读事务读取。

```text
id: 42
event: node.updated
data: {"seq":42,"run_id":"run_example","node_id":"node_example","status":"succeeded","completed_items":1,"total_items":1}

```

事件类型：`run.updated / node.updated / asset.ready / revision.stale / usage.updated / export.ready / reset.required`。每 15 秒发送注释 heartbeat；事件 payload 有大小上限；进度限频，状态变化及时提交。

workspace seq 在同空间提交顺序下分配，防止连接以较大 ID 前进后漏掉晚提交的小 ID。快照在一致读事务内读取领域状态与 watermark；返回的 cursor 不会早于其展示的业务状态。

历史保留建议 7 天；after 已过期时发 reset.required 并关闭，客户端重取快照，不循环空重连。会话退出/过期、账户禁用期间连接要在心跳检查时关闭。代理关闭 SSE buffering，空闲超时大于 heartbeat，服务端不为每个连接永久占用 DB session。

SSE 失效时前端 3/5/10 秒退避轮询任务摘要，隐藏页面降频；不无上限并发重试。事件 ID、事件格式和重连机制依据 [MDN SSE 文档](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events)。

## 9. 兼容与契约检查

M1–M2 中将前后端共同切到 v1，并从 OpenAPI 生成 TypeScript 类型；构建检查生成类型无漂移。旧接口仅用于演示数据迁移过渡，生产禁止 demo 用户回退。

核心契约测试：无身份访问、跨空间路径替换、同幂等键重放、ETag 冲突、已过期报价、重复上传完成、下载 Range、SSE 断线恢复和过期 cursor、旧任务不覆盖新选用。测试使用本机专用数据库及自建夹具。
