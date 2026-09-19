# 本地运行

当前开发切片使用本机 SQLite 和本机 FFmpeg，数据写入项目根目录下的 `.runtime/`（已加入 Git 忽略）。这是演示运行说明；规划中的正式认证、PostgreSQL 和完整生成链路尚未全部实现。

## 启动后端

```powershell
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## 启动前端

另开终端：

```powershell
cd apps/web
npm install
npm run dev
```

然后打开 `http://127.0.0.1:5173`。当前演示会话自动使用本地用户，不需要粘贴密钥。

## 验证

```powershell
cd apps/web
npm run build

cd ../../backend
python -m compileall -q app
Invoke-RestMethod http://127.0.0.1:8000/api/health
```

真实模型尚未接入时，页面会清楚显示本地演示模式；不要把演示结果当成供应商生成结果。
