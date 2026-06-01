# 智能城市生成系统 — 后端 API 文档 & 测试指南

> 后端地址：`http://localhost:8000`  
> 启动命令：`python -m uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload`  
> 前置环境变量：`DEEPSEEK_API_KEY`（文本 LLM）、`ZHIPU_API_KEY`（截图多模态）

---

## 1. 健康检查

```
GET /api/health
```

**测试（PowerShell）**：
```powershell
Invoke-RestMethod http://localhost:8000/api/health
```

**预期响应**：
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

**预期响应**：
```json
{
  "traceId": "trace-...",
  "data": {
    "token": "jwt-modeler-...",
    "user": { "id": "usr-modeler", "name": "林知远", "role": "modeler", ... },
    "expiresAt": "..."
  }
}
```

**测试（错误密码）**：
```powershell
$body = @{ email = "modeler@nku.city"; password = "wrong" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/auth/login -Method POST -Body $body -ContentType "application/json"
```
→ 应返回 `401`

---

## 3. 工作区

### 3.1 全量数据

```
GET /api/workspace/bundle
```

**测试**：
```powershell
Invoke-RestMethod http://localhost:8000/api/workspace/bundle | ConvertTo-Json -Depth 3
```

**预期**：`data.projects`、`data.scenes`、`data.tasks`、`data.functions` 等 12 个字段，`data.functions` 包含 28 个插件函数。

### 3.2 仪表盘

```
GET /api/dashboard/summary
```

**测试**：
```powershell
Invoke-RestMethod http://localhost:8000/api/dashboard/summary
```

**预期**：`projectTotal`、`runningTasks`、`failedTasks` 等字段。

---

## 4. 多模态交互（核心）

### 4.1 文本指令解析

```
POST /api/commands/submit?actor=林知远
```

**测试 1 — 道路+车道**：
```powershell
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  text = "把道路宽度调到10米，增加车道到4条"
  modalities = @("text")
  attachmentNames = @()
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：`data.plan` 包含 `set_street_width(width=10)` 和 `set_lane_amount(lanes=4)`。

**测试 2 — 天气+模板**：
```powershell
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  text = "切换成商业步行街模板，傍晚小雨天气"
  modalities = @("text")
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `apply_template_linkage` 和 `set_weather_lighting`。

**测试 3 — 生态场景**：
```powershell
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  text = "生成一个山丘地形，高度200米，再生成一个湖泊"
  modalities = @("text")
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `generate_terrain` 和 `generate_lake`。

**测试 4 — 交通仿真**：
```powershell
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  text = "对当前场景启动车辆与人群仿真，规则版本 traffic-r3.2"
  modalities = @("text")
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `run_traffic_simulation` 和 `run_crowd_simulation`。

**测试 5 — 家具资产**：
```powershell
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  text = "放置10个垃圾桶"
  modalities = @("text")
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：plan 包含 `place_furniture`。

**测试 6 — 空指令（应返回 needsClarification）**：
```powershell
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  text = "你好"
  modalities = @("text")
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：`data.needsClarification = true` 或 plan 为空。

### 4.2 截图多模态（需要 ZHIPU_API_KEY）

```
POST /api/commands/submit?actor=林知远
```

**测试**：
```powershell
$img = [Convert]::ToBase64String([IO.File]::ReadAllBytes("test.png"))
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  text = "分析这个城市场景截图"
  modalities = @("screenshot")
  attachmentNames = @("test.png")
  imageBase64 = $img
} | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 4
```

**预期**：GLM-4V-Flash 分析截图，返回场景相关的函数计划。

---

## 5. 计划下发

### 5.1 下发函数计划

```
POST /api/commands/{commandId}/dispatch?actor=林知远
```

**测试**：
```powershell
# 先拿到 commandId（从 submit 的响应 data.id）
$cmdId = "..."
Invoke-RestMethod -Uri "http://localhost:8000/api/commands/$cmdId/dispatch?actor=林知远" -Method POST | ConvertTo-Json -Depth 3
```

**预期**：`data` 为 Task 数组，每个 status 为 `queued`。

---

## 6. 任务编排

### 6.1 直接下发任务

```
POST /api/tasks/dispatch?actor=林知远
```

**测试**：
```powershell
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  functionName = "set_street_width"
  title = "设置道路宽度为8米"
  priority = 3
  params = @{ width = 8 }
  dependsOn = @()
} | ConvertTo-Json -Depth 3
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/dispatch?actor=林知远" -Method POST -Body $body -ContentType "application/json" | ConvertTo-Json -Depth 3
```

**预期**：返回 Task，`status = "queued"`。

### 6.2 重试任务

```
POST /api/tasks/{taskId}/retry?actor=林知远
```

**测试**：
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/task-1001/retry?actor=林知远" -Method POST
```

**预期**：任务 `status` 变为 `running`。

---

## 7. Blender 轮询同步

### 7.1 Blender 注册

```
POST /api/blender/register
```

**测试**：
```powershell
$body = @{ version = "2.8.0"; blender = "4.1" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/blender/register -Method POST -Body $body -ContentType "application/json"
```

**预期**：返回 pending 任务列表。

### 7.2 拉取待执行任务

```
GET /api/tasks/pending
```

**测试**：
```powershell
Invoke-RestMethod http://localhost:8000/api/tasks/pending | ConvertTo-Json -Depth 3
```

**预期**：返回 status=queued 的任务，且这些任务被标记为 running(10%)。

### 7.3 上报任务结果

```
POST /api/tasks/{taskId}/result
```

**测试**：
```powershell
$body = @{ status = "success"; results = @("道路宽度已设置") } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/tasks/task-1001/result" -Method POST -Body $body -ContentType "application/json"
```

**预期**：任务 `status = "success"`, `progress = 100`。

---

## 8. 项目与场景

### 8.1 创建项目

```
POST /api/projects?actor=林知远
```

**测试**：
```powershell
$body = @{
  name = "测试项目"
  cityScaleKm2 = 1.5
  coordinateSystem = "WGS84"
  tags = @("测试")
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/projects?actor=林知远" -Method POST -Body $body -ContentType "application/json"
```

**预期**：返回新 Project，附带默认 Scene。

### 8.2 更新场景模板

```
POST /api/scenes/template?actor=林知远
```

**测试**：
```powershell
$body = @{
  sceneId = "scn-river-main"
  templateId = "tpl-commercial"
  treeDensity = 60
  roadWidth = 10
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/scenes/template?actor=林知远" -Method POST -Body $body -ContentType "application/json"
```

**预期**：场景的 `treeType`/`roadType`/`seatType` 更新为法桐阵列/商业步行街断面/模块化金属座椅。

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

### 9.3 草图提取

```
POST /api/layout/extract-sketch?actor=林知远&projectId=prj-riverside&sceneId=scn-river-main&fileName=road.png
```

---

## 10. 版本与设置

### 10.1 创建快照 / 回滚

```
POST /api/versions/snapshot?actor=林知远
POST /api/versions/{id}/rollback?actor=admin
```

### 10.2 更新设置

```
PATCH /api/settings/set-llm-confidence?value=0.8&actor=admin
```

### 10.3 切换函数启用

```
PATCH /api/functions/set_street_width/toggle?enabled=true&actor=admin
```

---

## 11. 端到端测试流程

### 完整链路验证

```powershell
# Step 1: 健康检查
Invoke-RestMethod http://localhost:8000/api/health

# Step 2: 登录
$body = @{ email = "modeler@nku.city"; password = "demo1234" } | ConvertTo-Json
Invoke-RestMethod -Uri http://localhost:8000/api/auth/login -Method POST -Body $body -ContentType "application/json"

# Step 3: 提交指令
$body = @{
  projectId = "prj-riverside"
  sceneId = "scn-river-main"
  text = "把道路宽度调到10米，增加车道到4条，傍晚小雨"
  modalities = @("text")
  attachmentNames = @()
} | ConvertTo-Json
$resp = Invoke-RestMethod -Uri "http://localhost:8000/api/commands/submit?actor=林知远" -Method POST -Body $body -ContentType "application/json"
$cmdId = $resp.data.id
Write-Host "Command: $cmdId, Plan: $($resp.data.plan.Count) nodes"

# Step 4: 下发计划
$tasks = Invoke-RestMethod -Uri "http://localhost:8000/api/commands/$cmdId/dispatch?actor=林知远" -Method POST
Write-Host "Dispatched: $($tasks.data.Count) tasks"

# Step 5: 检查任务状态（Blender 轮询后会更新）
Start-Sleep -Seconds 10
(Invoke-RestMethod http://localhost:8000/api/workspace/bundle).data.tasks | Select-Object -First 3 | Format-Table id,functionName,status,progress
```

---

## 12. 函数完整列表（28 个）

### 成员 B — LLM 核心（14 个）
| 函数 | 参数 |
|------|------|
| `apply_template_linkage` | template_id, tree_density, road_width |
| `set_weather_lighting` | weather, time_of_day |
| `set_street_width` | width |
| `set_lane_amount` | lanes |
| `set_tree_density` | density |
| `set_sidewalk_scale` | scale |
| `set_corner_radius` | radius |
| `set_parking_probability` | probability |
| `set_street_lights` | enable |
| `set_traffic_lights` | probability |
| `set_building_height` | height |
| `set_seed` | seed |
| `toggle_traffic` | enable |
| `toggle_buildings` | enable |

### 成员 A — 资产模板（5 个）
| 函数 | 参数 |
|------|------|
| `apply_scene_template` | template_id (0-2) |
| `apply_road_texture` | texture_id |
| `apply_pavement_texture` | texture_id |
| `place_furniture` | asset_id, count, spacing, scale |
| `apply_layout_template` | layout_id, rows, columns |

### 成员 C — 生态场景（4 个）
| 函数 | 参数 |
|------|------|
| `generate_terrain` | hill_height, noise_scale, grid_size |
| `generate_lake` | lake_size, ripple_strength |
| `generate_river` | river_width, seed |
| `add_boat` | boat_scale, flow_speed |

### 成员 D — 仿真布局（5 个）
| 函数 | 参数 |
|------|------|
| `start_simulation` | car_density, pedestrian_density, car_speed_min/max |
| `stop_simulation` | — |
| `run_traffic_simulation` | rules_version, seed |
| `run_crowd_simulation` | rules_version, seed, agent_count |
| `apply_layout` | points |
| `sketch_layout` | image_path, threshold |
