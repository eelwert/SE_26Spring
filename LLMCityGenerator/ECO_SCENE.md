# Eco Scene Elements 功能文档

## 概述

在 LLM City Generator 侧边栏 "Eco Scene Elements" 面板下，提供四项生态化场景元素的程序化生成：山丘地形、湖泊区块、河流水面、船只停泊。

## 文件清单

| 文件 | 说明 |
|------|------|
| `panels/eco_panel.py` | 4 个面板（1 父 + 3 子） |
| `operators/eco_ops.py` | 4 个操作符 |
| `properties.py` | 注册 15+ 个 Scene 属性 |
| `CG_Park_Ground.png` | 烘焙的 CG 公园草地贴图（地形用） |
| `Wooden Boat.blend` | 外部木船模型（可选，无则回退程序化方块船） |

## Panel 结构

```
Eco Scene Elements  (CG_Eco_Scene_Panel)
  ├── Terrain       (CG_Eco_Terrain_Panel)
  ├── Lake          (CG_Eco_Lake_Panel)
  └── River & Boats (CG_Eco_River_Panel)
```

## 功能说明

### 1. Terrain — 山丘地形

**原理**：Grid 网格 → Subdivision Surface → Displace（Cloud 噪波 + Edge_Falloff 顶点组边缘衰减）→ 草地贴图材质。

**使用**：调整参数后点击 `Generate Terrain`。勾选 `Apply to City Grid` 可将地形位移同步到城市网格。

**关键参数**：Grid Size（默认 50m）、Hill Height、Noise Scale（越大山峰越少，默认 15）

**贴图**：`CG_Park_Ground.png` 不存在时回退到纯绿色材质。贴图通过 Object 坐标 + Mapping 节点平铺（默认 4 块/Grid）。

### 2. Lake — 湖泊区块

**原理**：1×1 单面平面 + CG 公园修改器（仅地面纹理 + 稀疏树木）→ 不规则圆形水面叠加。

**使用**：调整 Block Size / Lake Size / 种子等参数后点击 `Generate Lake`。

**关键参数**：Block Size（默认 30m）、Lake Size（默认 10m）、Edge Irregularity、Lake Seed

### 3. River — 河流水面

**原理**：6 点贝塞尔曲线（随机蜿蜒）→ 64 采样点转 Mesh → 左右偏移半河宽构建带状水面。

**使用**：点击 `Generate River`。不同 River Seed 生成不同蜿蜒形状。

**关键参数**：River Width（默认 3m）、River Seed

### 4. Boat — 船只停泊

**原理**：优先从 `Wooden Boat.blend` 加载外部模型（取顶点数最大的网格为主船体，其余部件为子物体），不存在则回退程序化方块船。船体放在河流中段随机位置，朝与水流切线一致。

**使用**：选中目标河流曲线，点击 `Add Boat`。每次点击随机换位。

**关键参数**：Boat Scale、Flow Speed（目前仅影响位置偏移量）

## Scene 属性清单

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `cg_terrain_hill_height` | Float | 60 | 山丘最大高度(m) |
| `cg_terrain_noise_scale` | Float | 15 | 噪波缩放（越大山峰越少） |
| `cg_terrain_noise_detail` | Int | 0 | 噪波细节（0=圆滑） |
| `cg_terrain_grid_size` | Float | 50 | 地形网格大小(m) |
| `cg_terrain_subdivisions` | Int | 30 | 网格细分密度 |
| `cg_terrain_detail_enabled` | Bool | False | 启用第二层噪波细节 |
| `cg_terrain_detail_height` | Float | 5 | 细节层高度(m) |
| `cg_terrain_apply_to_city` | Bool | False | 同步位移到城市网格 |
| `cg_lake_block_size` | Float | 30 | 湖泊区块大小(m) |
| `cg_lake_size` | Float | 10 | 湖面半径(m) |
| `cg_lake_edge_irregularity` | Float | 0.3 | 湖岸线不规则度 |
| `cg_lake_seed` | Int | 0 | 湖岸线随机种子 |
| `cg_lake_vertices` | Int | 32 | 湖面顶点数 |
| `cg_lake_ripple_strength` | Float | 0.05 | 波纹法线强度 |
| `cg_lake_ripple_scale` | Float | 2 | 波纹噪波缩放 |
| `cg_lake_water_color` | Color | (0.05,0.2,0.4) | 水面颜色 |
| `cg_river_width` | Float | 3 | 河流宽度(m) |
| `cg_river_seed` | Int | 0 | 河流蜿蜒种子 |
| `cg_river_flow_speed` | Float | 1 | 流速 |
| `cg_boat_scale` | Float | 1 | 船体缩放 |

## 依赖与注意事项

- 首次使用前需通过 `Import City Generator` 导入 `City_Generator_2.0` 节点组和资产集合
- 地形贴图需手动烘焙：创建 CG 公园小平面 → 正交俯拍渲染 → 保存为 `CG_Park_Ground.png`
- 木船模型 `Wooden Boat.blend` 为可选外部资产，放在 `LLMCityGenerator/` 目录下即可自动加载
- 生成的对象可自由移动、旋转、缩放；河流曲线和湖面是其父物体的子节点，整体移动父物体即可
