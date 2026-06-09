# 建筑区块重叠检测与前端可视化文档

## 概述

`building_control` 模块管理 LLM 可控制的独立 CG 区块。每个区块是一个带 `City_Generator_2.0` 修改器的单面 Mesh，在 XY 平面上占据一个矩形区域。模块通过**网格化空间哈希 + AABB 精确重叠检测**确保区块不会相互重叠。

本文档供前端开发者参考，用于在网页端以矩形方格形式展示区块分布。

## 1. 坐标系统

```
        Y+
        |
        |
        +------ X+
      原点 (0,0)
```

区块使用**中心坐标**表示：`(x, y)` 是区块底面的几何中心。`width` 沿 X 轴方向延伸，`depth` 沿 Y 轴方向延伸。由此可推导出区块的轴对齐包围盒（AABB）：

```
左下角:  (x - width/2,  y - depth/2)
右上角:  (x + width/2,  y + depth/2)
```

所有坐标单位为**米**，这是 Blender 的标准单位。Z 轴（高度）不参与重叠检测——重叠判断仅在 XY 平面进行，因为建筑之间的冲突只取决于底面投影。

## 2. 数据接口

### `list_buildings` 返回格式

调用 `execute_function("list_buildings", {}, context)` 返回：

```json
{
  "success": true,
  "results": ["共 3 栋受控建筑:", "  B_0001: ...", "  B_0002: ...", "  B_0003: ..."],
  "data": {
    "buildings": [
      {
        "id": "B_0001",
        "x": -30.0, "y": 0.0,
        "width": 15.0, "depth": 15.0, "height": 50.0,
        "color": ""
      },
      {
        "id": "B_0002",
        "x": -30.0, "y": 30.0,
        "width": 12.0, "depth": 12.0, "height": 25.0,
        "color": ""
      }
    ],
    "count": 2
  }
}
```

`data.buildings` 数组是前端可视化的核心数据源。`color` 字段当前保留但未使用（CG 修改器自行决定外观），前端可忽略或预留为未来扩展。

### `query_space` 查询接口

前端在用户拖拽放置新区块前，可以调用 `query_space` 实时检测目标区域是否可用：

```json
// 请求
{"x": 100, "y": 80, "width": 15, "depth": 15}

// 响应（可用）
{
  "success": true,
  "data": {"available": true, "conflict_id": null}
}

// 响应（冲突）
{
  "success": true,
  "data": {"available": false, "conflict_id": "B_0001"}
}
```

## 3. 重叠检测算法

### AABB 重叠判断

两个轴对齐矩形 A 和 B 不重叠的充要条件是以下四者之一成立：
- A 完全在 B 的左侧：`A.x + A.w < B.x`
- B 完全在 A 的左侧：`B.x + B.w < A.x`
- A 完全在 B 的下方：`A.y + A.d < B.y`
- B 完全在 A 的下方：`B.y + B.d < A.y`

取反即得重叠条件。Python 实现：

```python
def aabb_overlap(ax, ay, aw, ad, bx, by, bw, bd):
    return not (
        ax + aw < bx or   # A 在 B 左侧
        bx + bw < ax or   # B 在 A 左侧
        ay + ad < by or   # A 在 B 下方
        by + bd < ay      # B 在 A 下方
    )
```

其中 `ax`, `ay` 是矩形左下角坐标（即 `x - width/2`, `y - depth/2`），`aw`, `ad` 是宽度和深度。

注意：边界相接**不视为重叠**。两个区块并排贴在一起（一个的右边界等于另一个的左边界）是允许的。

### 网格化空间哈希（加速查询）

直接对 N 个建筑逐一检测的复杂度为 O(N)。空间哈希将其优化到接近 O(1)：

1. 将 XY 平面按 `CELL_SIZE = 10m` 划分为网格单元，每个单元用整数坐标 `(gx, gy)` 标识
2. 每个建筑注册时，计算其 AABB 覆盖的所有网格单元，在这些单元中记录该建筑 ID
3. 查询新区块时，只需检查其覆盖的网格单元中的候选建筑，而非全局遍历

```
+---------+---------+---------+
|         | B_0001  |B_0001   |
|         |(覆盖格子|(覆盖格子 |
|         | (1,0))  | (2,0))  |
+---------+---------+---------+
|         | B_0001  |B_0001   |
|         |(覆盖格子|(覆盖格子 |
|         | (1,1))  | (2,1))  |
+---------+---------+---------+
```

如上图，`B_0001`（15m×15m）覆盖了 4 个 10m 网格单元。查询重叠时，仅检索这 4 个单元中的建筑 ID，再逐一对候选建筑做 AABB 精确检测。

## 4. 前端可视化建议

### 在 2D Canvas 上绘制建筑矩形

从 `list_buildings` 获取数据后，前端可按如下伪代码渲染：

```
for each building in buildings:
    left   = building.x - building.width / 2
    top    = building.y - building.depth / 2   // Y轴正方向朝上
    // 或 bottom = building.y - building.depth / 2（取决于画布坐标方向）

    drawRect(
        x = toCanvasX(left),
        y = toCanvasY(top),       // 注意 Y 轴方向翻转
        w = building.width  * scale,
        h = building.depth   * scale,
        color = "#4488CC",
        label = building.id,
    )
```

### 画布坐标映射

Blender 使用右手坐标系（X 右、Y 上），前端 Canvas 通常 Y 轴朝下。映射公式：

```
toCanvasX(blender_x) = origin_x + blender_x * pixelsPerMeter
toCanvasY(blender_y) = origin_y - blender_y * pixelsPerMeter   // Y 翻转
```

### 拖拽放置时的实时冲突预览

用户拖拽新区块时，前端可实时调用 `query_space`，根据 `data.available` 切换矩形颜色（绿色=可用、红色=冲突），并在冲突时高亮 `conflict_id` 对应的既有区块。

### 推荐缩放

典型城市尺度在 -200m 到 +200m 范围。若 Canvas 为 800×800 像素，`pixelsPerMeter ≈ 2.0`。建议提供缩放和平移控件以适应不同尺度的场景。

## 5. 实现文件索引

| 文件 | 作用 |
|------|------|
| `LLMCityGenerator/building_control/spatial_index.py` | `GridSpatialIndex` 类，AABB 检测 + 网格哈希 |
| `LLMCityGenerator/building_control/building_registry.py` | `BuildingRegistry` 单例 + `BuildingRecord` 数据类 |
| `LLMCityGenerator/building_control/building_api.py` | `_handle_list_buildings`、`_handle_query_space` 等 handler |
