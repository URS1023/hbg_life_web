# ADR-0002：数据库驱动工作流与显式恢复

状态：Proposed。日期：2026-09-19。

## 背景

当前 SQLite 队列可保留未执行任务，但执行中无租约，付费请求、重复投递、取消和异常恢复没有完整记录。产品需要单镜头恢复与费用核对。

## 决策

PostgreSQL 保存 run/node/attempt/provider_request、outbox、事件和额度；Celery + Redis 负责投递；Worker 使用 lease 与 fencing token 写回。供应商状态未知时进入 reconciling，不保证外部调用恰好一次。

幂等键、预算预留和创建任务同事务；outbox 修复事务/消息断点，过期 queued 扫描覆盖 broker 丢消息，过期 running 扫描先核对外部状态。长任务分队列，异步供应商等待不占 Worker。

## 比较与代价

- 继续用进程内 asyncio 会随 API 重启丢执行上下文，不适合作为正式任务系统。
- 只用数据库轮询可减少组件，但需自行实现投递与执行生态；沿用已有 Celery 方向，数据库负责业务恢复。
- Temporal 提供持久执行能力，但当前固定流程规模下先引入其服务和开发模型会增加投入。未来复杂长生命周期流程可复审。
- Celery 不消除幂等、账务和供应商核对责任；显式状态机需要充分边界测试，不能只验证 happy path。

## 验证依据

参考 [Celery task 重投递/幂等说明](https://docs.celeryq.dev/en/stable/userguide/tasks.html) 与 [Redis broker 注意事项](https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/redis.html)。验收对应 TASK-01 至 TASK-07 和 COST 全套。
