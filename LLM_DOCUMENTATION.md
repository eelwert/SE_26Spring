# 智能城市生成系统 — 项目文档

> 成员 B（任务 7）：LLM 自然语言控制 + 后端控制平面
> 最后更新：2026-06-03

---

## 一、从零启动

### 1. 环境变量（PowerShell）

```powershell
$env:DEEPSEEK_API_KEY = "sk-你的DeepSeekKey"          # 文本指令解析
$env:QWEN_API_KEY = "sk-你的阿里云DashScope Key"        # 草图识别
$env:ZHIPU_API_KEY = "你的智谱API Key"                  # 截图分析
```

### 2. 安装依赖

```powershell
# Python 后端
pip install fastapi uvicorn pydantic pillow

# 前端
cd C:\Users\CHDN\Desktop\SE\SE_26Spring
npm install
```

### 3. 启动后端

```powershell
cd C:\Users\CHDN\Desktop\SE\SE_26Spring
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 启动前端

```powershell
cd C:\Users\CHDN\Desktop\SE\SE_26Spring
npm run dev
```

浏览器打开 `http://localhost:5173`

### 5. Blender 插件

插件随 Blender 5.1 自动加载。首次或更新代码后，在 Blender Python 控制台（Shift+F11）重载：

```python
from bl_ext.user_default.LLMCityGenerator import unregister, register
unregister()
register()
```

---

## 二、架构总览

```
前端 React (:5173)             后端 FastAPI (:8000)           Blender 插件
─────────────────────        ─────────────────────────        ─────────────────────
MultimodalPage.tsx      →    POST /api/commands/submit   →   llm_service.py
  [文本/草图/截图]              ├─ sketch → Qwen-VL-Plus         function_registry.py
  WorkspaceContext             ├─ screenshot → GLM-4V           blender_sync.py (轮询)
  ↓ dispatchPlan               └─ text → DeepSeek
                               ↓ POST /api/tasks/dispatch
任务轮询 ← GET /api/tasks/pending ← Blender 3s 轮询
                               → POST /api/tasks/{id}/result ← 执行结果上报
```

### 三级解析回退（文本）

DeepSeek API → curl 回退 → 本地关键词解析（`parse_local()`）

### 草图识别模型链

QWEN_VISION_MODEL (`qwen-vl-plus`) → `SKETCH_ANALYSIS_PROMPT` 系统提示词

---

## 三、文件清单

### Blender 插件

| 文件 | 功能 |
|------|------|
| `function_registry.py` | 28 个可调用函数，参数 Schema + Blender handler |
| `llm_service.py` | DeepSeek API 调用、System Prompt、JSON 解析、curl 回退、本地解析 |
| `blender_sync.py` | 后台轮询后端任务队列，主线程执行，结果上报 |
| `operators/llm_ops.py` | 发送→解析→执行 LLM 指令 |
| `operators/layout_ops.py` | Preview/Apply 点集布局 + Generate from Sketch 草图识别 |
| `panels/llm_panel.py` | LLM 侧边栏面板 |
| `panels/layout_panel.py` | 道路布局控制面板（Points/Connections/Faces + 草图上传） |
| `layout/sketch_processor.py` | 草图分析（raw socket HTTP → 后端 → Qwen-VL） |
| `properties.py` | 场景属性注册（LLM + 生态 + 动态仿真 + 布局） |

### 后端

| 文件 | 功能 |
|------|------|
| `server.py` | FastAPI 主应用，CORS，WebSocket |
| `schemas.py` | Pydantic 模型 |
| `store.py` | 内存数据存储 + 演示种子数据 |
| `routes/api.py` | 所有 REST API 端点（含 `/sketch/analyze`） |
| `llm_service.py` | LLM 服务（文本 + 截图 + 草图三种通路） |
| `ws_manager.py` | WebSocket 管理 |

### 前端

| 文件 | 功能 |
|------|------|
| `src/pages/MultimodalPage.tsx` | 多模态交互页面（文本/草图/截图） |
| `src/services/api/index.ts` | `USE_REAL_API` 切换开关 |
| `src/services/api/realApi.ts` | fetch 调用后端 |
| `src/context/WorkspaceContext.tsx` | 3s HTTP 轮询任务更新 |

---

## 四、所有功能测试

### 4.1 文本指令 — Blender 面板

在 Blender 侧边栏 `LLM City Generator` 中输入：

- 道路："把道路宽度调到12米，增加车道到6条"
- 天气模板："切换成滨水商业街区模板，傍晚小雨天气"
- 生态："生成一个山丘地形，高度200米"
- 仿真："启动车辆人流仿真，车辆密度20"
- 家具："放置8个野餐椅"
- 建筑："建筑高度设为30米"

点击 **Send to LLM** → 查看解析结果 → 自动执行到 Blender。

### 4.2 文本指令 — 前端 → Blender（端到端）

1. 确保后端 + 前端 + Blender 均启动
2. 前端 `http://localhost:5173` → 多模态智能交互
3. 输入指令文本 → 点 **解析指令**
4. 查看右侧函数 DAG 计划
5. 点 **自动下发** → Blender 自动拉取执行

### 4.3 草图识别 — Blender 面板

1. Blender 侧边栏 → **Road Layout Control**
2. Sketch Image → 选择根目录的测试草图（`sketch_cross.png` / `sketch_tian.png` 等）
3. 点 **Generate from Sketch**
4. LLM 识别结果自动填入 Points/Connections/Faces 输入框
5. 审查调整 → 点 **Preview** 预览 → 点 **Apply** 生成道路

### 4.4 草图识别 — 前端 → Blender（端到端）

1. 前端多模态页面 → 勾选 **草图**（自动取消截图）
2. 上传道路草图图片
3. 可选填文本指令 → 点 **解析指令**
4. 查看函数计划（`apply_layout`）→ 点 **自动下发**
5. Blender 拉取执行 → 自动填入面板 → Apply

### 4.5 截图分析 — 前端

1. 前端多模态页面 → 勾选 **截图**
2. 上传城市场景截图
3. 点 **解析指令** → GLM-4V 分析截图内容
4. 查看返回的函数计划（天气、建筑高度、树木密度等）

### 4.6 手动点集布局

Blender Road Layout Control 面板：

- Points：`0,0;80,0;0,80;80,80;0,160;80,160`
- Faces：`0,1,3,2;2,3,5,4`
- 点 Preview → Apply

### 4.7 后端 API 独立测试

见 [BACKEND_API.md](BACKEND_API.md) ，所有端点有 PowerShell 测试命令。

---

## 五、测试草图文件

根目录提供以下测试草图：

| 文件 | 形状 | 预期识 |
|------|------|--------|
| `sketch_cross.png` | 十字路口 | 5 点 4 边（AI 应扩展为 9 点 4 面田字形） |
| `sketch_ri.png` | 日字形 | 6 点 2 面 |
| `sketch_tian.png` | 田字形 | 9 点 4 面 |
| `sketch_mu.png` | 目字形 | 8 点 3 面 |
| `sketch_T.png` | T字路口 | 4 点 3 边 |
| `sketch_L.png` | L形折线 | 3 点 2 边 |
| `sketch_Y.png` | Y字分叉 | 4 点 3 边 |
| `sketch_straight.png` | 单条道路 | 2 点 1 边 |
| `sketch_triangle.png` | 三角环路 | 3 点 3 边 |

---

## 六、函数注册表（28 个）

### 成员 B — LLM 核心（14 个）

| 函数 | 功能 | Socket/属性 | 参数 |
|------|------|------------|------|
| `apply_template_linkage` | 模板联动 | Socket_9,159 | template_id(0-9), tree_density, road_width |
| `set_weather_lighting` | 天气天色 | World 灯光 | weather, time_of_day |
| `set_street_width` | 道路宽度 | Socket_9 | width(米) |
| `set_lane_amount` | 车道数量 | Socket_12 | lanes |
| `set_tree_density` | 树木密度 | Socket_159,172 | density(0-1) |
| `set_sidewalk_scale` | 人行道缩放 | Socket_16 | scale |
| `set_corner_radius` | 路口圆角 | Socket_22 | radius(米) |
| `set_parking_probability` | 停车道概率 | Socket_20 | probability(0-1) |
| `set_street_lights` | 路灯开关 | Socket_64(bool) | enable |
| `set_traffic_lights` | 交通灯概率 | Socket_83 | probability(0-1) |
| `set_building_height` | 建筑高度 | Custom_Height 属性 | height(米) |
| `set_seed` | 随机种子 | Socket_21 | seed |
| `toggle_traffic` | 交通开关 | Socket_144 | enable |
| `toggle_buildings` | 建筑开关 | Socket_142 | enable |

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

### 成员 A — 资产模板（6 个）

| 函数 | 参数 | 说明 |
|------|------|------|
| `apply_scene_template` | template_id (0-2) | 场景模板 |
| `apply_road_texture` | texture_id | 道路纹理 |
| `apply_pavement_texture` | texture_id | 人行道纹理 |
| `place_furniture` | asset_id, min/max_count, spacing, scale, randomize, placement_offset, clear_previous | 放置 3D 家具（野餐椅/小消防罐/小黄鸭） |
| `delete_furniture` | asset_id | 删除新增家具 |
| `apply_layout_template` | layout_id, rows, columns | 布局模板 |

### 成员 C — 生态场景（4 个）

| 函数 | 参数 | 说明 |
|------|------|------|
| `generate_terrain` | hill_height, noise_scale, grid_size, subdivisions | 生成山丘地形 |
| `generate_lake` | lake_size, ripple_strength | 生成湖泊 |
| `generate_river` | river_width, seed | 生成河流 |
| `add_boat` | boat_scale, flow_speed | 添加船只 |

### 成员 D — 仿真布局（6 个）

| 函数 | 参数 | 说明 |
|------|------|------|
| `start_simulation` | car_density, pedestrian_density, car_speed_min/max | 启动仿真 |
| `stop_simulation` | — | 停止仿真 |
| `run_traffic_simulation` | rules_version, seed | 车辆仿真 |
| `run_crowd_simulation` | rules_version, seed, agent_count | 人群仿真 |
| `apply_layout` | points, connections, faces | 应用道路布局（文本格式） |
| `sketch_layout` | image_path, threshold | 草图提取（旧） |

---

## 七、全部 API 端点（21 个）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/health` | 健康检查 |
| POST | `/api/auth/login` | 登录 |
| GET | `/api/workspace/bundle` | 全量数据 |
| GET | `/api/dashboard/summary` | 仪表盘 |
| POST | `/api/projects` | 创建项目 |
| POST | `/api/scenes/template` | 更新场景模板 |
| POST | `/api/assets/replace` | 替换资产 |
| POST | `/api/layout/solve` | 点集布局 |
| POST | `/api/layout/extract-sketch` | 草图提取（旧） |
| POST | `/api/commands/submit` | 多模态指令提交（文本/草图/截图） |
| POST | `/api/commands/{id}/dispatch` | 计划下发 |
| POST | `/api/tasks/dispatch` | 直接下发任务 |
| POST | `/api/tasks/{id}/retry` | 重试任务 |
| POST | `/api/sketch/analyze` | 草图分析（独立接口） |
| POST | `/api/simulations/start` | 启动仿真 |
| PATCH | `/api/simulations/{id}` | 更新仿真状态 |
| POST | `/api/versions/snapshot` | 创建快照 |
| POST | `/api/versions/{id}/rollback` | 回滚版本 |
| PATCH | `/api/settings/{id}` | 更新设置 |
| PATCH | `/api/functions/{name}/toggle` | 切换函数启用 |
| POST | `/api/blender/register` | Blender 注册 |
| GET | `/api/tasks/pending` | 拉取待执行任务 |
| POST | `/api/tasks/{id}/result` | 上报任务结果 |

---

## 八、关键技术点

- **Socket 访问**：`obj.modifiers[name][socket_id] = value` 完整 RNA 路径赋值，后调用 `obj.update_tag()` + `view_layer.update()` 强制刷新 GN
- **Bool 类型**：`bool("false")` 在 Python 中为 `True`，用 `_to_bool()` 安全转换
- **Blender 网络**：内置 Python 被防火墙拦截，用 `subprocess` 调系统 `curl` 或 raw socket HTTP
- **线程安全**：后台线程只做 HTTP 轮询，任务推入列表，主线程 timer (0.5s) 执行
- **数值安全**：`_safe_float`/`_safe_int` 处理 LLM 返回的字符串值（如 `"medium"`→10）
- **草图识别**：Blender raw socket → 后端 → Qwen-VL-Plus 多模态 → 返回 Points/Connections/Faces 文本
- **多模态互斥**：前端草图/截图二选一，后端走不同通路
