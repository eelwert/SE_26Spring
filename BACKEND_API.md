# 智能城市生成系统 — 后端 API 文档 & 测试指南

> 后端地址：`http://localhost:8000`
> 启动命令：`python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload`
> 环境变量：`DEEPSEEK_API_KEY`（文本 LLM）、`ZHIPU_API_KEY`（截图分析）、`QWEN_API_KEY`（草图识别）

---

## 1. 健康检查

```
GET /api/health
```

**测试（PowerShell）**：

```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

**预期**：

```json
{"status":"ok","blender":"connected","frontend":"connected"}
```

---

## 2. 认证

### 2.1 登录

```
POST /api/auth/login
```

**测试**：

```powershell
$body = @{ email = "modeler@nku.city"; password = "demo1234" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/auth/login -Method POST -Body $body -ContentType "application/json"
```

**预期**：返回 `token` + `user` 对象。错误密码返回 `401`。

---

## 3. 工作区

### 3.1 全量数据

```
GET /api/workspace/bundle
```

```powershell
Invoke-RestMethod http://localhost:8000/api/workspace/bundle | ConvertTo-Json -Depth 3
```

**预期**：`data.functions` 包含 28 个插件函数。

### 3.2 仪表盘

```
GET /api/dashboard/summary
```

```powershell
Invoke-RestMethod http://localhost:8000/api/dashboard/summary
```

---

## 4. 多模态交互（核心）

### 4.1 文本指令解析

```
POST /api/commands/submit?actor=林知远
```

Body: `projectId`, `sceneId`, `text`, `modalities: ["text"]`

**测试 1 — 道路+车道**：

```powershell
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = "把道路宽度调到10米，增加车道到4条"; modalities = @("text"); attachmentNames = @() } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `set_street_width(width=10)` + `set_lane_amount(lanes=4)`。

**测试 2 — 天气+模板**：

```powershell
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = "切换成商业步行街模板，傍晚小雨天气"; modalities = @("text") } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `apply_template_linkage` + `set_weather_lighting`。

**测试 3 — 生态场景**：

```powershell
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = "生成一个山丘地形，高度200米，再生成一个湖泊"; modalities = @("text") } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `generate_terrain` + `generate_lake`。

**测试 4 — 交通仿真**：

```powershell
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = "启动车辆与人群仿真，规则版本 traffic-r3.2"; modalities = @("text") } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `run_traffic_simulation` + `run_crowd_simulation`。

**测试 5 — 家具资产**：

```powershell
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = "放置5个野餐椅"; modalities = @("text") } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `place_furniture(asset_id="wooden_picnic_table")`。

### 4.2 截图多模态（需要 ZHIPU_API_KEY）

```
POST /api/commands/submit
```

Body: `modalities: ["screenshot"]`, `imageBase64: "<base64>"`

```powershell
$img = [Convert]::ToBase64String([IO.File]::ReadAllBytes("test.png"))
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = ""; modalities = @("screenshot"); attachmentNames = @("test.png"); imageBase64 = $img } | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：GLM-4V 分析截图，返回场景相关的函数计划。

### 4.3 草图识别（需要 QWEN_API_KEY）

```
POST /api/commands/submit
```

Body: `modalities: ["sketch"]`, `imageBase64: "<base64>"`

```powershell
$img = [Convert]::ToBase64String([IO.File]::ReadAllBytes("sketch_cross.png"))
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = ""; modalities = @("sketch"); attachmentNames = @("sketch_cross.png"); imageBase64 = $img } | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：`intentTag = "sketch_layout"`，plan 包含 `apply_layout`，params 含 `points`/`connections`/`faces` 文本。

### 4.4 草图分析（独立接口）

```
POST /api/sketch/analyze
```

Body: `{"image_base64": "<base64>"}`

```powershell
$img = [Convert]::ToBase64String([IO.File]::ReadAllBytes("sketch_cross.png"))
$body = @{ image_base64 = $img } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/sketch/analyze" -Method POST -Body $body -ContentType "application/json"
```

**预期**：返回 `points_text`/`connections_text`/`faces_text` 三个分号分隔的文本字符串。

---

## 5. 计划下发

```
POST /api/commands/{commandId}/dispatch?actor=林知远
```

```powershell
$cmdId = "cmd-xxxx"
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/$cmdId/dispatch?actor=林知远" -Method POST | ConvertTo-Json -Depth 3
```

**预期**：返回 Task 数组，status = `queued`。

---

## 6. 任务编排

### 6.1 直接下发任务

```
POST /api/tasks/dispatch?actor=林知远
```

```powershell
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; functionName = "set_street_width"; title = "道路宽度8米"; priority = 3; params = @{ width = 8 }; dependsOn = @() } | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/dispatch?actor=林知远" -Method POST -Body $body -ContentType "application/json"
```

### 6.2 重试任务

```
POST /api/tasks/{taskId}/retry?actor=林知远
```

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/task-1001/retry?actor=林知远" -Method POST
```

---

## 7. Blender 轮询同步

### 7.1 注册

```
POST /api/blender/register
```

```powershell
$body = @{ version = "2.8.0"; blender = "5.1" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/blender/register -Method POST -Body $body -ContentType "application/json"
```

### 7.2 拉取待执行任务

```
GET /api/tasks/pending
```

```powershell
Invoke-RestMethod http://localhost:8000/api/tasks/pending | ConvertTo-Json -Depth 3
```

**预期**：返回 status=queued 的任务，并标记为 running(10%)。

### 7.3 上报任务结果

```
POST /api/tasks/{taskId}/result
```

```powershell
$body = @{ status = "success"; results = @("道路宽度已设置") } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/task-1001/result" -Method POST -Body $body -ContentType "application/json"
```

**预期**：任务 status="success", progress=100。

---

## 8. 项目与场景

### 8.1 创建项目

```
POST /api/projects?actor=林知远
```

```powershell
$body = @{ name = "测试项目"; cityScaleKm2 = 1.5; coordinateSystem = "WGS84"; tags = @("测试") } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/projects?actor=林知远" -Method POST -Body $body -ContentType "application/json"
```

### 8.2 更新场景模板

```
POST /api/scenes/template?actor=林知远
```

```powershell
$body = @{ sceneId = "scn-river-main"; templateId = "tpl-commercial"; treeDensity = 60; roadWidth = 10 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/scenes/template?actor=林知远" -Method POST -Body $body -ContentType "application/json"
```

---

## 9. 资产与布局

### 9.1 替换资产

```
POST /api/assets/replace?actor=林知远
```

### 9.2 点集布局

```
POST /api/layout/solve?actor=林知远
```

### 9.3 草图提取（旧接口，已废弃）

```
POST /api/layout/extract-sketch
```

---

## 10. 仿真

### 10.1 启动

```
POST /api/simulations/start
```

### 10.2 更新状态

```
PATCH /api/simulations/{id}?status=completed
```

---

## 11. 版本与设置

### 11.1 快照 / 回滚

```
POST /api/versions/snapshot?actor=林知远
POST /api/versions/{id}/rollback?actor=admin
```

### 11.2 更新设置

```
PATCH /api/settings/set-llm-confidence?value=0.8&actor=admin
```

### 11.3 切换函数

```
PATCH /api/functions/set_street_width/toggle?enabled=true&actor=admin
```

---

## 12. 端到端测试

```powershell
# 1. 启动后端
$env:DEEPSEEK_API_KEY = "sk-xxx"
$env:QWEN_API_KEY = "sk-xxx"
$env:ZHIPU_API_KEY = "xxx"
python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload

# 2. 健康检查
Invoke-RestMethod http://localhost:8000/api/health

# 3. 文本指令
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = "道路宽度10米，4条车道，傍晚小雨"; modalities = @("text"); attachmentNames = @() } | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json"
$cmdId = $resp.data.id

# 4. 下发
$tasks = Invoke-RestMethod -Uri "http://localhost:8000/api/commands/$cmdId/dispatch?actor=林知远" -Method POST

# 5. 草图识别
$img = [Convert]::ToBase64String([IO.File]::ReadAllBytes("sketch_cross.png"))
$body = @{ projectId = "prj-riverside"; sceneId = "scn-river-main"; text = ""; modalities = @("sketch"); attachmentNames = @("sketch_cross.png"); imageBase64 = $img } | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json"
```

---

## 13. 函数完整列表（28 个）

### 成员 B — LLM 核心（14 个）

| 函数 | 参数 | 说明 |
|------|------|------|
| `apply_template_linkage` | template_id, tree_density, road_width | 模板联动 |
| `set_weather_lighting` | weather, time_of_day | 天气天色 |
| `set_street_width` | width | 道路宽度(米) |
| `set_lane_amount` | lanes | 车道数量 |
| `set_tree_density` | density | 树木密度(0-1) |
| `set_sidewalk_scale` | scale | 人行道缩放 |
| `set_corner_radius` | radius | 路口圆角半径 |
| `set_parking_probability` | probability | 停车概率 |
| `set_street_lights` | enable | 路灯开关 |
| `set_traffic_lights` | probability | 交通灯概率 |
| `set_building_height` | height | 建筑高度(米) |
| `set_seed` | seed | 随机种子 |
| `toggle_traffic` | enable | 交通开关 |
| `toggle_buildings` | enable | 建筑开关 |

### 成员 A — 资产模板（6 个）

| 函数 | 参数 | 说明 |
|------|------|------|
| `apply_scene_template` | template_id (0-2) | 场景模板 |
| `apply_road_texture` | texture_id | 道路纹理 |
| `apply_pavement_texture` | texture_id | 人行道纹理 |
| `place_furniture` | asset_id, min/max_count, spacing, scale, randomize, placement_offset, clear_previous | 放置家具 |
| `delete_furniture` | asset_id | 删除家具 |
| `apply_layout_template` | layout_id, rows, columns | 布局模板 |

### 成员 C — 生态场景（4 个）

| 函数 | 参数 | 说明 |
|------|------|------|
| `generate_terrain` | hill_height, noise_scale, grid_size | 生成山丘地形 |
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
| `apply_layout` | points, connections, faces | 应用道路布局 |
| `sketch_layout` | image_path, threshold | 草图提取 |
