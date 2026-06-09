# 测试说明

本文档说明当前项目已有的测试内容、覆盖范围和运行方式。项目包含 Blender 插件、FastAPI 后端、React 前端和 LLM/多模态能力，因此测试也按层级拆分。

## 测试目录

```text
tests/
├── backend/
│   ├── conftest.py                 # FastAPI TestClient 与后端内存数据重置
│   ├── test_api_contract.py         # 后端 REST API 契约测试
│   ├── test_ai_integration.py       # 真实 AI provider 集成测试
│   ├── test_blender_contract.py     # Blender 插件协议/manifest/脚本生成测试
│   ├── test_llm_service.py          # LLM fallback 与 JSON 解析测试
│   └── test_smoke.py                # pytest 基础 smoke test
├── unit/
│   ├── App.test.tsx                 # React 登录、角色、权限路由测试
│   └── ui.test.tsx                  # 共享 UI 组件测试
├── e2e/
│   ├── app.spec.ts                  # Playwright mock E2E 测试
│   └── overall.spec.ts              # 真实前端 + 真实后端 + 假 Blender 的整体测试
└── setup.ts                         # Vitest/jest-dom 初始化
```

## 后端测试

工具：`pytest` + FastAPI `TestClient`

运行：

```powershell
python -m pytest
```

只运行后端 API 契约测试：

```powershell
python -m pytest tests/backend/test_api_contract.py
```

覆盖内容：

- 登录成功/失败和健康检查。
- workspace bundle 和 dashboard summary。
- 项目创建、场景模板更新、资产替换。
- 点集布局、草图拓扑任务。
- 任务下发、重试、Blender pending 队列、任务回执。
- 多模态命令提交、命令计划下发、澄清保护。
- 仿真启动/完成。
- 版本快照和回滚。
- 设置更新、锁定设置保护、插件函数启停。
- `/sketch/analyze` 的错误路径和无 key fallback。

目前后端 REST API 基本全覆盖；`/ws/frontend` 已通过整体 E2E 间接覆盖，`/ws/blender` 尚未单独自动化覆盖。

## LLM 测试

LLM 测试分两类：默认稳定测试和真实 AI 集成测试。

默认 LLM 测试：

```powershell
python -m pytest tests/backend/test_llm_service.py
```

覆盖内容：

- 无 `DEEPSEEK_API_KEY` 时，本地关键词解析 fallback。
- 文本指令解析道路宽度、车道、天气、模板。
- 仿真指令解析车辆/人群仿真。
- 未知文本返回 `needsClarification=true`。
- 无 `QWEN_API_KEY` 时，草图识别返回需要澄清。
- LLM 返回 JSON 外带额外文本时，后端能提取 JSON。

真实 AI 集成测试：

```powershell
python -m pytest tests/backend/test_ai_integration.py
```

需要的环境变量：

```powershell
$env:DEEPSEEK_API_KEY = "你的 DeepSeek key"
$env:QWEN_API_KEY = "你的 DashScope/Qwen key"
$env:ZHIPU_API_KEY = "你的 Zhipu key"
```

说明：

- 有对应 key 时，测试会真实调用该 provider。
- 没有对应 key 时，只跳过该 provider 的测试。
- 临时跳过所有真实 AI 测试：

```powershell
$env:SKIP_AI_INTEGRATION = "1"
python -m pytest
```

查看 AI 原始返回：

```powershell
$env:AI_DEBUG_RAW = "1"
python -m pytest tests/backend/test_ai_integration.py -s
```

真实 AI 测试覆盖：

- DeepSeek：自然语言文本解析为函数计划。
- Qwen：草图图片识别为点、边、面拓扑文本。
- Zhipu：截图/视觉输入解析为函数计划。

## Blender 协议测试

运行：

```powershell
python -m pytest tests/backend/test_blender_contract.py
```

覆盖内容：

- `LLMCityGenerator/blender_manifest.toml` 声明插件 ID、类型和最低 Blender 版本。
- 后端生成的 Blender 执行脚本会调用 `LLMCityGenerator.function_registry.execute_function`。
- 插件注册入口会启动后端同步轮询 `start_sync()`。

注意：这些是协议/契约测试，不是在真实 Blender 中执行所有插件函数。真实 Blender 函数执行测试需要安装 Blender、启用插件并准备场景上下文。

## 前端单元测试

工具：Vitest + React Testing Library

运行：

```powershell
npm run test:run
```

开发监听模式：

```powershell
npm run test
```

覆盖内容：

- 未登录访问受保护路由会跳转登录页。
- modeler 登录进入“场景建模师门户”。
- analyst 登录进入“行业分析师门户”。
- admin 登录进入“系统管理员门户”。
- modeler 访问 `/settings` 会被重定向回 `/modeler`。
- 共享 UI 组件 `StatusBadge`、`ProgressBar`。

前端单测通过 mock `src/services/api` 隔离真实后端，不依赖 FastAPI、LLM 或 Blender。

## E2E 测试

工具：Playwright

运行：

```powershell
npm run test:e2e
```

只运行整体测试：

```powershell
npx playwright test tests/e2e/overall.spec.ts --project=chromium
```

Playwright 会自动启动 Vite dev server：

```text
http://127.0.0.1:5173
```

覆盖内容：

- 登录页可以打开。
- modeler 登录进入 `/modeler`。
- analyst 登录进入 `/analyst`。
- admin 登录进入 `/admin`。
- modeler 访问管理员设置页会被权限守卫重定向。

`tests/e2e/app.spec.ts` 使用 Playwright route mock 拦截 `**/api/**`，因此不依赖真实后端、LLM 或 Blender，主要验证登录、角色门户和权限路由。

`tests/e2e/overall.spec.ts` 是当前项目的整体测试：

- 启动真实 FastAPI 后端和真实前端。
- 清空 `DEEPSEEK_API_KEY`、`QWEN_API_KEY`、`ZHIPU_API_KEY`，强制后端走本地 fallback LLM。
- 从前端多模态页面提交真实文本指令，由后端生成函数计划并自动下发任务。
- 测试代码通过 `/api/blender/register`、`/api/tasks/pending`、`/api/tasks/{id}/result` 模拟 Blender 拉取任务和回执。
- 前端通过 `/ws/frontend` 接收实时任务状态更新，并在页面上显示成功结果。

这条整体测试不依赖真实 LLM 或真实 Blender，但已经覆盖真实前端、真实后端、任务队列、假 Blender 回执和前端 WebSocket 刷新。

## 性能测试

已补充基础性能测试，位置：

```text
tests/backend/test_performance_basic.py
```

运行：

```powershell
python -m pytest tests/backend/test_performance_basic.py
```

只运行性能基线测试：

```powershell
python -m pytest -m performance
```

覆盖内容：

- 核心 API 延迟基线：`POST /api/auth/login`、`GET /api/workspace/bundle`、`GET /api/dashboard/summary`
- 本地 fallback LLM 解析延迟：`POST /api/commands/submit`
- 实时更新延迟：`POST /api/tasks/{id}/result` 到 `/ws/frontend` 收到 `task_update`

说明：

- 这些测试属于轻量性能基线测试，不是并发压测或长稳测试。
- 当前阈值用于约束本地开发环境和 CI 中的明显性能回退。
- 由于项目当前大量逻辑基于内存 store 和本地 TestClient，这些测试更适合作为回归基线，而不是最终生产容量评估。

## 构建与 lint

前端构建：

```powershell
npm run build
```

ESLint：

```powershell
npm run lint
```

当前 lint 可能出现 React Fast Refresh warning，来源是 context 文件同时导出 Provider 和 hook；这是警告，不是测试失败。

## 推荐运行顺序

日常快速验证：

```powershell
python -m pytest
npm run test:run
npx playwright test tests/e2e/overall.spec.ts --project=chromium
```

提交前完整验证：

```powershell
python -m pytest
npm run test:run
npm run build
npm run lint
npm run test:e2e
```

带真实 AI key 的后端验证：

```powershell
$env:DEEPSEEK_API_KEY = "你的 DeepSeek key"
$env:QWEN_API_KEY = "你的 DashScope/Qwen key"
$env:ZHIPU_API_KEY = "你的 Zhipu key"
python -m pytest
```

## 当前尚未覆盖的测试

- WebSocket `/ws/blender`。
- 真实 Blender 中逐个执行 `function_registry` 的 28 个插件函数。
- 前端连接真实 Blender 插件的浏览器 E2E。
- 后端 + 真实 Blender 插件轮询 + 场景执行的完整集成测试。

这些属于下一阶段集成测试，依赖 Blender 安装、插件启用和可用场景文件。

## 常见问题

### pytest 出现 `.pytest_cache` 权限 warning

这不影响测试结果。可临时禁用 pytest cache：

```powershell
python -m pytest -p no:cacheprovider
```

### 真实 AI 测试失败怎么办

先打开原始返回：

```powershell
$env:AI_DEBUG_RAW = "1"
python -m pytest tests/backend/test_ai_integration.py -s
```

检查：

- key 是否配置在当前 PowerShell 会话。
- provider 是否返回非 JSON 或多个 JSON。
- 字段是否满足后端要求，例如 `plan`、`funcName`、`params`。
- 是否是网络、额度、模型服务临时问题。

### key 放哪里

当前后端直接读取环境变量，不自动读取 `.env`。不要把真实 key 写进代码或提交到 Git。
