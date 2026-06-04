# 智能城市生成系统前端

这是智能城市生成系统的 React + TypeScript + Vite 前端。当前版本默认连接真实 FastAPI 后端，不再自动回退 mock 数据。

## 启动

先启动后端：

```bash
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

再启动前端：

```bash
npm install
npm run dev
```

默认访问：

```text
http://localhost:5173
```

## 后端配置

默认后端地址：

```text
http://localhost:8000
```

如需修改地址，可设置 Vite 环境变量：

```bash
VITE_BACKEND_ORIGIN=http://localhost:8000
VITE_API_BASE_URL=http://localhost:8000/api
VITE_WS_URL=ws://localhost:8000/ws/frontend
```

前端不会静默切换到 mock。后端未启动或不可达时，页面会显示连接错误和后端启动命令。

## 账号

登录页提供三类演示账号：

- 场景建模师：`modeler@nku.city` / `demo1234`
- 行业分析师：`analyst@nku.city` / `demo1234`
- 系统管理员：`admin@nku.city` / `demo1234`

## 结构

- `src/services/api`：真实后端 API 客户端与运行时地址配置。
- `src/types`：领域类型、DTO 与状态枚举。
- `src/context`：会话与业务数据上下文。
- `src/pages`：登录、工作台、项目场景、任务编排、多模态、仿真、审计版本、系统设置。
- `src/components`：布局、通用 UI 与业务可视化组件。

## 验证

```bash
npm run build
```
