# ADR-0004：服务端会话与私人空间

状态：Proposed。日期：2026-09-19。

## 背景

浏览器是首版唯一正式客户端；当前 `Bearer` 直接传用户 ID 的模式只适合演示。下载、SSE、批量生成和素材库均需要同样的归属控制。

## 决策

邀请制账户使用密码摘要和服务端不透明会话，Cookie 为 HttpOnly/Secure/SameSite，并配 CSRF/Origin 验证。每个账户一个私人 workspace；查询、引用、上传、下载及事件都按空间授权。

P0 使用受约束 repository 与复合外键，配跨空间负向测试；RLS 留作后续纵深保护，启用前单独验证数据库角色和连接池事务上下文。平台管理员的管理能力与读取私人内容权限分离。

## 比较与代价

- JWT 适合部分独立客户端场景，但浏览器首版无此必需条件；服务端会话更直接支持撤销、禁用和同源媒体/SSE。
- 每用户独立数据库的运维成本不适合首版；共享表必须严格限定 workspace 并验证批量边界。
- 单靠应用授权可能出现漏过滤，因此强制数据访问封装、复合引用约束和系统性隔离用例均属于 P0。

## 验收与依据

AUTH-01 至 AUTH-04、FILE-02、EVT-01 通过。遵循 [OWASP 会话管理](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) 的 Cookie/撤销原则；RLS 的角色例外依据 [PostgreSQL 文档](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)。
