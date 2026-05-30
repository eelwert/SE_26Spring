# LLM 自然语言控制 — 项目文档

> 成员 B（任务 7）：LLM 自然语言控制 + Phase 2 后端控制平面

---

## 一、架构总览

```
前端 React (src/)              后端 FastAPI (backend/)           Blender 插件 (LLMCityGenerator/)
─────────────────────        ─────────────────────────        ────────────────────────────────
MultimodalPage.tsx      →    POST /api/commands/submit   →   llm_service.py (LLM 解析)
  submitCommand()             →   DeepSeek / GLM-4V 调用      ↓
  dispatchPlan()         ←    POST /api/commands/dispatch →  blender_client.py (任务下发)
                              
任务白名单 ← store.py functions[]          function_registry.py (14 个 handler)
```

**三级解析回退**：DeepSeek API → curl 回退 → 本地关键词解析

---

## 二、文件清单

### Blender 插件（4 个新建）

| 文件 | 功能 |
|------|------|
| `LLMCityGenerator/function_registry.py` | 14 个可调用函数，参数 Schema + Blender 执行 handler |
| `LLMCityGenerator/llm_service.py` | DeepSeek API 调用、System Prompt、JSON 解析、curl 回退、本地解析 |
| `LLMCityGenerator/operators/llm_ops.py` | `cg.execute_llm_command`（发送→解析→执行链）+ `cg.clear_llm_result` |
| `LLMCityGenerator/panels/llm_panel.py` | 侧边栏面板：API Key、指令输入、快捷示例、可滚动结果列表 |

### 后端（7 个新建）

| 文件 | 功能 |
|------|------|
| `backend/server.py` | FastAPI 主应用，CORS 配置 |
| `backend/schemas.py` | Pydantic 模型，对应 `src/types/domain.ts` 所有类型 |
| `backend/store.py` | 内存数据存储 + 演示种子数据 |
| `backend/routes/api.py` | 18 个 REST API 端点 |
| `backend/llm_service.py` | LLM 服务（文本 + 多模态截图分析） |
| `backend/blender_client.py` | Blender CLI 驱动（`blender --background --python`） |
| `src/services/api/realApi.ts` | 前端真实 API 客户端（fetch 调用后端） |

### 修改的文件

| 文件 | 变更 |
|------|------|
| `LLMCityGenerator/__init__.py` | 注册 6 个新类 |
| `LLMCityGenerator/properties.py` | 新增 CG_LLMResultLine + 8 个 LLM 场景属性 |
| `LLMCityGenerator/operators/__init__.py` | 导出 LLM 操作符 |
| `LLMCityGenerator/panels/__init__.py` | 导出 LLM 面板 |
| `src/services/api/index.ts` | `USE_REAL_API` 切换开关 |

---

## 三、函数注册表（14 个可调用函数）

| 函数名 | 功能 | Socket/属性 | 参数 |
|--------|------|------------|------|
| `apply_template_linkage` | 模板联动 | Socket_9,159 | `template_id`(0-9), `tree_density`, `road_width` |
| `set_weather_lighting` | 天气天色 | 场景 World 灯光 | `weather`, `time_of_day` |
| `set_street_width` | 道路宽度 | Socket_9 | `width`(米) |
| `set_lane_amount` | 车道数量 | Socket_12 | `lanes` |
| `set_tree_density` | 树木密度 | Socket_159,172 | `density`(0-1) |
| `set_sidewalk_scale` | 人行道缩放 | Socket_16 | `scale` |
| `set_corner_radius` | 路口圆角 | Socket_22 | `radius`(米) |
| `set_parking_probability` | 停车道概率 | Socket_20 | `probability`(0-1) |
| `set_street_lights` | 路灯开关 | Socket_64(bool) | `enable` |
| `set_traffic_lights` | 交通灯概率 | Socket_83 | `probability`(0-1) |
| `set_building_height` | 建筑高度 | Custom_Height 属性 | `height`(米) |
| `set_seed` | 随机种子 | Socket_21 | `seed` |
| `toggle_traffic` | 交通开关 | Socket_144 | `enable` |
| `toggle_buildings` | 建筑开关 | Socket_142 | `enable` |

### 模板 ID 映射

| ID | 名称 | 树木 | 道路 | 座椅 |
|----|------|------|------|------|
| 0 | 默认 | 默认 | 默认 | 默认 |
| 1 | 滨水活力街区 | 国槐+银杏 | 慢行优先断面 | 滨水木质长椅 |
| 2 | 商业步行街 | 法桐阵列 | 商业步行街断面 | 模块化金属座椅 |
| 3 | 枢纽换乘片区 | 低维护乔木 | 公交优先断面 | 候车廊一体座椅 |
| 4 | 校园安全疏散 | 白蜡+灌木 | 校园混行道路 | 校园石材座椅 |
| 5 | 生态公园 | 柳树+水生 | 慢行优先断面 | 自然石材座椅 |
| 6 | 科技园区 | 银杏阵列 | 现代简洁断面 | 几何金属座椅 |
| 7 | 历史街区 | 古槐保留 | 窄街巷断面 | 仿古木质座椅 |
| 8 | 住宅社区 | 樱花+桂花 | 生活性道路 | 庭院式座椅 |
| 9 | 工业物流区 | 抗污染乔木 | 宽幅货运道路 | 简约混凝土座椅 |

---

## 四、API 端点（18 个）

### 认证
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录，演示账号 `modeler@nku.city` / `demo1234` |

### 工作区
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/workspace/bundle` | 全量数据拉取 |
| GET | `/api/dashboard/summary` | 仪表盘摘要 |

### 项目
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/projects` | 创建项目 |
| POST | `/api/scenes/template` | 更新场景模板 |

### 资产
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/assets/replace` | 批量资产替换 |

### 布局
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/layout/solve` | 点集布局求解 |
| POST | `/api/layout/extract-sketch` | 草图点线提取 |

### 任务编排
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/tasks/dispatch` | 下发任务到 Blender |
| POST | `/api/tasks/{id}/retry` | 重试失败任务 |

### 多模态交互 ★核心
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/commands/submit` | 提交 NL 指令/截图，返回函数计划 |
| POST | `/api/commands/{id}/dispatch` | 下发函数计划为任务队列 |

### 仿真
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/simulations/start` | 启动仿真 |
| PATCH | `/api/simulations/{id}` | 更新仿真状态 |

### 版本
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/versions/snapshot` | 创建场景快照 |
| POST | `/api/versions/{id}/rollback` | 版本回滚 |

### 设置
| 方法 | 路径 | 说明 |
|------|------|------|
| PATCH | `/api/settings/{id}` | 更新运行参数 |
| PATCH | `/api/functions/{name}/toggle` | 启用/禁用插件函数 |

---

## 五、多模态支持

| 通道 | API 模型 | 状态 |
|------|---------|------|
| 文本 | DeepSeek `deepseek-chat` | ✅ 已实现 |
| 截图 | 智谱 `glm-4v-flash` | ✅ 后端已实现 |
| 草图 | 待对接成员 D | ⏳ 等待 OpenCV 模块 |

---

## 六、启动方式

### 1. 启动后端

```powershell
$env:DEEPSEEK_API_KEY = "你的DeepSeek Key"
$env:ZHIPU_API_KEY = "你的智谱 Key"
cd C:\Users\CHDN\Desktop\SE\SE_26Spring
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 前端切到真实 API

`src/services/api/index.ts`：

```typescript
const USE_REAL_API = true;  // false = mock, true = 真实后端
```

### 3. 启动前端

```bash
npm run dev
```

浏览器打开 `http://localhost:5173`

### 4. 验证后端

```bash
curl http://localhost:8000/api/health
# → {"status":"ok"}
```

---

## 七、验证清单

| 序号 | 验证项 | 方法 |
|------|--------|------|
| 1 | 登录 | modeler@nku.city / demo1234 |
| 2 | 文本 NL 解析 | 输入"把道路宽度调到10米，增加车道到4条"，点解析指令 |
| 3 | 函数 DAG 显示 | 右侧出现 set_street_width + set_lane_amount 计划节点 |
| 4 | 计划下发 | 点"自动下发"，关联任务区出现任务卡片 |
| 5 | LLM 实际调用 | 设 DEEPSEEK_API_KEY 后提交，后端终端打印 LLM 返回 |
| 6 | 截图分析 | POST `/api/commands/submit` 带 imageBase64 |
| 7 | Blender 插件 | 在 Blender 侧边栏输入指令，点 Send to LLM |
| 8 | 模板切换 | "切换成滨水商业街区" |
| 9 | 天气设置 | "傍晚小雨天气" |
| 10 | 树木密度 | "树木密度设为0.3" |

---

## 八、待完成

| 项 | 说明 | 依赖 |
|----|------|------|
| 多模型支持 | 接入智谱 GLM-4 文本模型 | 加一行配置 |
| 草图分析对接 | OpenCV 提取拓扑 + LLM 解析 | 成员 D 任务 10 |
| 仿真切实执行 | `run_traffic_simulation` 等 handler | 成员 D 任务 8 |
| 生态场景对接 | 湖泊/地形 handler | 成员 C 任务 9 |
| Blender 实时通信 | WebSocket 替代 CLI 调用 | Phase 2 后续 |

---

## 九、关键技术点

- **Socket 访问**：通过 `obj.modifiers[name][socket_id] = value` 完整 RNA 路径赋值，后调用 `obj.update_tag()` + `view_layer.update()` 强制刷新 GN 修改器
- **Bool 类型陷阱**：Socket_64（路灯）是 `bool` 不是 float，`bool("false")` 在 Python 中为 `True`，需用 `_to_bool()` 安全转换
- **网络回退**：Blender 内置 Python 可能被防火墙拦截，通过 `subprocess` 调用系统 `curl` 作为回退
- **图标兼容**：Blender 4.1 图标集比 4.3 少，需避免使用新图标名
