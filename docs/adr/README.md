# 架构决策索引

日期：2026-09-19。以下为本轮技术方案的建议决策，状态 Proposed，尚不代表已经实施或通过真实集成验收。后续实施任务采纳时记录 Accepted 和证据；重大改动通过新 ADR 取代，保留原判断依据。

| ADR | 决策 | 状态 |
| --- | --- | --- |
| [0001](./0001-modular-monolith.md) | 延续 Vue/FastAPI，模块化单体和独立 Worker | Proposed |
| [0002](./0002-durable-workflow.md) | PostgreSQL 持久状态、Celery 投递和显式恢复 | Proposed |
| [0003](./0003-versioned-media.md) | 不可变生成快照、私有媒体和统一 RenderManifest | Proposed |
| [0004](./0004-session-and-workspace.md) | 服务端会话与私人空间隔离 | Proposed |

方案总入口：[technical-design.md](../technical-design.md)。
