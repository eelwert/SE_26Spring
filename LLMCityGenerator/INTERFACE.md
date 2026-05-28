# City Generator 接口文档

本文档总结了 [__init__.py](__init__.py) 中对外可见的 Blender 插件接口，作为 UI、操作符和 Geometry Nodes 集成的稳定契约。

## 插件元数据

- 名称: The City Generator
- Blender: 4.3.0
- 类别: Object
- UI 入口: View3D > Sidebar > City Generator

## 常量与资源

- `ADDON_DIR`: 插件目录路径。
- `BLEND_FILE`: City_Generator2.0.blend（资源库）。
- 代码中引用的资源名称:
  - Object: City_Generator_2.0_Object
  - Geometry Nodes 组: City_Generator_2.0
  - Collection: City_Gen_2.0_Assets
  - Materials: CityGen car material, CityGen_Red_Emission, CityGen_Green_Emission, CityGen_Blue_Emission, CityGenLamp_Emission, CityGen_Yellow_Emission
  - Node group: street light color
  - 室内材质: CityGen_Interior_Room_Shader, CityGen_Interior_Office_Shader, CityGen_Interior_Store_Shader

## 工具函数

- `append_data(directory, filename)`
  - 通过 `bpy.ops.wm.append` 从 City_Generator2.0.blend 追加资源。
- `get_or_create_attribute(mesh, name, attr_type, domain)`
  - 确保网格自定义属性存在并返回该属性。
- `find_layer_collection(layer_collection, collection_name)`
  - 递归查找指定名称的 Layer Collection。

## 操作符 (bpy.types.Operator)

- `cg.import_node_group`
  - 导入 City_Generator_2.0_Object 与 City_Generator_2.0 节点组。
  - 将 City_Gen_2.0_Assets 从视图层排除。
- `cg.apply_node_group`
  - 触发条件: 对象模式、存在激活的网格对象。
  - 确保 City_Generator_2.0 节点组存在，并添加 Geometry Nodes 修改器。
  - 将 City_Gen_2.0_Assets 从视图层排除。
- `cg.duplicate_object`
  - 复制带 City_Generator_2.0 修改器的激活对象。
  - 将复制体重命名为 CityGen Buildings，应用修改器后再重新添加。
  - 切换 Socket: `Socket_163`, `Socket_142`, `Socket_145`。

网格属性类操作符（仅编辑模式；对选择元素写入 INT 属性值）:
- `mesh.set_low_poly_attribute`
  - 属性: `low poly` (FACE)
- `mesh.add_park_attribute`
  - 属性: `assign Park` (FACE)
- `mesh.set_intersection_grid`
  - 属性: `add intersection grid` (POINT)
- `mesh.delete_crosswalk`
  - 属性: `delete cross walk` (POINT)
- `mesh.add_bus_lane`
  - 属性: `add bus lane` (EDGE)
- `mesh.delete_trees_from_edge`
  - 属性: `delete Trees from Edge` (EDGE)
- `mesh.set_modern_building_attribute`
  - 属性: `modern building` (FACE)
- `mesh.delete_building_attribute`
  - 属性: `Delete Building` (FACE)

## 面板 (bpy.types.Panel)

所有面板位于 View3D > Sidebar > City Generator。

- `CG_PT_Main_Panel`
  - 入口操作: Import City Generator, Apply Node Group。
- `CG_Setting_Panel`
  - 设置面板的父容器。
- `CG_General_Setting_Panel`
  - 布局编辑开关、元素开关、复制/建筑控制。
- `CG_Street_Setting_Panel`
  - 道路宽度、车道数量、种子等。
- `CG_Park_Setting_Panel`（`CG_Street_Setting_Panel` 子面板）
  - 公园分配操作与路径/树木控制。
- `CG_Street_Adv_Setting_Panel`（`CG_Street_Setting_Panel` 子面板）
  - 高级道路控制（斑马线、车道、灯光、资产、交通灯）。
- `CG_Traffic_Sim_Panel`（`CG_Setting_Panel` 子面板）
  - 模拟缓存操作、车辆分布、材质与资产集合。
- `CG_Building_Panel`（`CG_Setting_Panel` 子面板）
  - 建筑高度与资产选择。
- `CG_Building_Advanced_Panel`（`CG_Building_Panel` 子面板）
  - 面级自定义属性工具与 Z-shape 控制。
- `CG_Building_Asset_distribution_Panel`（`CG_Building_Advanced_Panel` 子面板）
  - 资产分布设置。
- `CG_Building_Floor_Plan_Shape_Panel`（`CG_Building_Advanced_Panel` 子面板）
  - 平面形状控制。
- `CG_Building_Additional_Assets_Panel`（`CG_Building_Advanced_Panel` 子面板）
  - 额外资产（消防梯、旗帜、脚手架）。
- `CG_Building_Roof_Panel`（`CG_Building_Advanced_Panel` 子面板）
  - 屋顶材质与屋顶资产控制。
- `CG_Night_Lighting_Panel`（`CG_Setting_Panel` 子面板）
  - 路灯颜色渐变与发光控制。
- `InteriorPanel`（`CG_Night_Lighting_Panel` 子面板）
  - 室内视差材质控制。

## Scene 属性 (bpy.types.Scene)

在 `register()` 中注册:
- `height_value` (Int, 0..1000) -> `update_customheight`
- `custom_facade_asset_index` (Int, 0..500) -> `update_custom_facade_asset_index`
- `custom_ground_asset` (Int, 0..500) -> `update_custom_ground_asset_index`
- `assign_low_poly` (Int, 0..500) -> `update_custom_ground_asset_index`
- `zshape` (Int, 0..500) -> `update_zshape_amount`
- `zshape_height` (Int, 0..500) -> `update_zshape_height`
- `zshape_insert` (Float, -0.75..500, subtype DISTANCE) -> `update_zshape_insert`

在 `add_custom_properties()` 中注册:
- `room_seed` (Float, 0..100)
- `close_roller_shutter` (Float, 0..1)
- `close_curtains` (Float, 0..1)
- `curtain_shutter_seed` (Float, 0..100)
- `randomise_hue` (Float, 0..1)
- `change_hue` (Float, -1..1)
- `emission_strength` (Float, 0..100)
- `light_probability` (Float, 0..1)
- `seed` (Float, 0..100)

已定义但未在 `register()` 中调用:
- `global_emission_strength` (Float, 0..100) 来自 `add_emission_properties()`

## 选择集属性更新

这些 update 回调会在选中元素上写入自定义网格属性:
- `update_customheight` -> `Custom_Height` (FACE, INT)
- `update_custom_facade_asset_index` -> `custom Facade Asset index` (FACE, INT)
- `update_custom_ground_asset_index` -> `custom Ground Floor Asset index` (FACE, INT)
- `update_zshape_amount` -> `Zshape Amount` (FACE, INT)
- `update_zshape_height` -> `Zshape Height` (FACE, INT)
- `update_zshape_insert` -> `Zshape insert` (FACE, FLOAT)

## 处理器

- `frame_change_pre` -> `frame_change_handler` -> `update_parallax_settings`
  - 根据场景属性更新室内材质节点输入。

## UI 绑定的 Geometry Nodes Socket

UI 通过 Socket ID 绑定到 Geometry Nodes 修改器，这些 ID 必须与 City_Generator_2.0 的节点组接口一致:

- 通用: `Socket_8`, `Socket_142`, `Socket_143`, `Socket_144`, `Socket_165`, `Socket_187`, `Socket_188`
- 道路: `Socket_9`, `Socket_12`, `Socket_16`, `Socket_20`, `Socket_21`
- 道路高级:
  - 道路形状: `Socket_22..Socket_25`
  - 贴花: `Socket_26`, `Socket_27`
  - 树木: `Socket_166..Socket_173`, `Socket_182..Socket_186`
  - 斑马线: `Socket_29..Socket_32`
  - 车道: `Socket_35..Socket_40`, `Socket_44..Socket_49`, `Socket_50`
  - 停车: `Socket_51..Socket_53`
  - 路口网格: `Socket_54..Socket_56`
  - 人行道: `Socket_59`, `Socket_60`
  - 路灯: `Socket_62..Socket_68`
  - 人行道资产: `Socket_69..Socket_74`
  - 护栏: `Socket_75..Socket_81`
  - 交通灯: `Socket_82..Socket_85`
- 公园: `Socket_154..Socket_162`
- 交通模拟: `Socket_89..Socket_109`
- 建筑: `Socket_112..Socket_120`
- 建筑分布: `Socket_116..Socket_119`
- 平面形状: `Socket_122..Socket_126`
- 额外资产: `Socket_128..Socket_140`
- 屋顶: `Socket_147..Socket_149`, `Socket_164`, `Socket_174..Socket_181`
- 复制操作切换: `Socket_163`, `Socket_145`

## 动态模拟系统（Dynamic Simulation）

`dynamics/` 包提供了独立于 Geometry Nodes 的 Python 驱动的动态元素系统。基于网格边（路网）提取道路曲线，生成车辆、行人和交通灯，通过帧回调驱动动画。

### 包结构

```
dynamics/
├── __init__.py              # 导出 + get_simulation_manager()
├── function_api.py          # ★ LLM 可调用的函数接口 + 参数 Schema + dispatch 入口
├── road_analyzer.py         # RoadAnalyzer: 网格边 → Bezier 曲线
├── car_system.py            # CarManager: 车辆生成 + 直接位置更新
├── pedestrian_system.py     # PedestrianManager: 行人 + 人行道路径
├── traffic_light.py         # TrafficLightManager: 路口检测 + 红绿灯周期
└── simulation_manager.py    # SimulationManager 单例 + bpy.app.timers 驱动
```

### 新增操作符

- `cg.add_dynamic_elements`
  - 触发条件: OBJECT 模式、选中 mesh 对象
  - 从选中 mesh 的边提取道路曲线，生成车辆、行人、交通灯
  - 结果收集在 `Dynamic_Traffic` 集合下
- `cg.remove_dynamic_elements`
  - 删除所有动态模拟对象（车辆、行人、交通灯、曲线）
  - 移除 `Dynamic_Traffic` 集合及其子集合

### 新增面板

- `CG_PT_Dynamics_Panel`（`CG_Setting_panel` 子面板）
  - 标题: "Dynamic Simulation"，默认折叠
  - 按钮: Add Dynamic Elements / Remove Dynamic Elements
  - 车辆参数: Car Density (0-200), Min Speed (1-50 m/s), Max Speed (1-50 m/s)
  - 行人参数: Pedestrian Density (0-200), Walking Speed (0.5-5 m/s)
  - 交通灯参数: Green Duration (30-600 frames), Yellow Duration (10-120), Red Duration (30-600)

### 新增 Scene 属性

在 `properties.py` 中注册（`cg_` 前缀）:
- `cg_car_density` (Int, 0..200, default 10)
- `cg_car_speed_min` (Float, 1.0..50.0, default 5.0)
- `cg_car_speed_max` (Float, 1.0..50.0, default 15.0)
- `cg_pedestrian_density` (Int, 0..200, default 5)
- `cg_pedestrian_speed` (Float, 0.5..5.0, default 1.5)
- `cg_traffic_light_green` (Int, 30..600, default 120)
- `cg_traffic_light_yellow` (Int, 10..120, default 30)
- `cg_traffic_light_red` (Int, 30..600, default 120)
- `cg_dynamics_active` (Bool, default False)

### 生成的对象集合

所有 Python 生成的动态对象位于 `Dynamic_Traffic` 父集合下:
- `Dynamic_Traffic_Paths` — 从 mesh 边提取的双向车道 Bezier 曲线
- `Dynamic_Sidewalk_Paths` — 人行道偏移曲线（道路两侧各一条）
- `Dynamic_Pedestrians` — 行人对象（彩色圆柱体，直接定位到人行道曲线上）
- `Dynamic_Traffic_Lights` — 交通灯对象（球体 + 发光材质，位于路口上方）

车辆由 Geo Nodes 原生仿真直接在场景中实例化，不走 Python 系统。

### 自定义属性

所有动态对象携带 `cg.*` 自定义属性用于帧回调驱动:
- 车辆: `cg.is_car`, `cg.car_speed`, `cg.car_direction`, `cg.car_curve`, `cg.car_offset`, `cg.car_curve_length`, `cg.car_stopped`, `cg.car_edge_id`
- 行人: `cg.is_pedestrian`, `cg.ped_speed`, `cg.ped_direction`, `cg.ped_curve`, `cg.ped_offset`, `cg.ped_curve_length`, `cg.ped_stopped`, `cg.ped_edge_id`
- 交通灯: `cg.is_traffic_light`, `cg.tl_intersection_id`, `cg.tl_edge_id`, `cg.tl_green`, `cg.tl_yellow`, `cg.tl_red`, `cg.tl_phase_offset`, `cg.tl_state`, `cg.tl_material`
- 路径: `cg.is_road_path`, `cg.edge_index`, `cg.road_length`

### 驱动方式

**纯 Python 驱动**（`bpy.app.timers` ~30 Hz）：汽车、行人、交通灯均由 Python 系统统一管理。
- 每 tick：更新交通灯状态 → 驱动汽车位置 → 推进行人位置 → `bpy.context.view_layer.update()`
- 汽车和行人通过 `CarManager.place_on_curve()` 直接设置 `obj.location` / `obj.rotation_euler`
- 不再依赖 Geo Nodes 仿真缓存

### LLM 函数 API (`function_api.py`)

供成员 B 的 `function_registry.py` 直接导入。所有函数返回统一格式：`{"success": bool, "data": ..., "message": str}`。

#### 可用函数

| functionName | 功能 | 关键参数 |
|---|---|---|
| `run_traffic_simulation` | 启动车辆仿真 | `car_density`, `speed_min`, `speed_max`, `traffic_lights` |
| `run_crowd_simulation` | 启动行人仿真 | `pedestrian_density`, `walking_speed`, `traffic_lights` |
| `run_full_simulation` | 同时启动车+行人+交通灯 | 以上所有参数 + `green_duration`, `yellow_duration`, `red_duration` |
| `stop_simulation` | 停止仿真并清理 | 无 |
| `set_traffic_light_timing` | 调整交通灯周期 | `green`, `yellow`, `red` (帧数) |
| `get_simulation_status` | 查询仿真状态 | 无 |

#### 成员 B 集成方式

```python
# 方式 1: 直接导入注册表
from LLMCityGenerator.dynamics.function_api import FUNCTION_REGISTRY
# FUNCTION_REGISTRY 是一个 dict，key = functionName，value = {function, description, params}

# 方式 2: 使用 dispatch 入口
from LLMCityGenerator.dynamics.function_api import dispatch_blender_job
result = dispatch_blender_job("run_full_simulation", {"car_density": 20})
# result = {"success": True, "data": {...}, "message": "..."}

# 方式 3: 直接调用具体函数
from LLMCityGenerator.dynamics.function_api import run_traffic_simulation
result = run_traffic_simulation(mesh_obj=bpy.context.object, params={"car_density": 15})
```

#### 返回格式

```python
# 成功
{"success": True, "data": {"car_count": 24, "road_count": 24}, "message": "24 cars on 24 roads"}

# 失败
{"success": False, "message": "Simulation already active. Call stop_simulation() first."}
```

### Python API 调用示例

```python
# 获取管理器单例
from dynamics.simulation_manager import SimulationManager
sim = SimulationManager.get_instance()

# 手动设置（通常由操作符或 function_api 完成）
sim.setup(bpy.context.active_object, enable_cars=True, enable_pedestrians=False)

# 手动清除
SimulationManager.reset_instance()

# 单独模块使用
from dynamics.road_analyzer import RoadAnalyzer
roads = RoadAnalyzer.extract_roads(mesh_obj)
RoadAnalyzer.cleanup_road_curves()
```

## 道路布局系统（Road Layout）

`layout/` 包提供道路布局的两种生成方式：手动坐标输入和手绘草图提取。输出为 mesh 对象（vertices=路口，edges=道路），可作为 City Generator 和动态仿真的输入。

### 包结构

```
layout/
├── __init__.py              # 导出
├── point_solver.py          # PointSolver: 坐标点 → mesh
├── sketch_processor.py      # SketchProcessor: 图像 → 线段 → mesh（cv2/LLM 双模式）
└── layout_api.py            # LLM 可调用函数 + 参数 Schema
```

### 新增操作符

- `cg.preview_point_layout` — 解析坐标文本，创建预览 mesh
- `cg.apply_point_layout` — 解析坐标，应用为正式道路布局 mesh
- `cg.apply_sketch_layout` — 加载草图 → 提取线条 → 创建 mesh

### 新增面板

- `CG_PT_Layout_Panel`（`CG_Setting_panel` 子面板）
  - 标题: "Road Layout Control"，默认折叠
  - 坐标输入: 文本输入框（格式 `x,y;x,y;...`）+ Preview / Apply 按钮
  - 草图输入: 文件选择器 + Threshold (0.1-1.0) + Min Length (5-500) + 生成按钮

### 新增 Scene 属性

- `cg_layout_points_text` (String, 坐标文本)
- `cg_sketch_image_path` (String, FILE_PATH, 草图路径)
- `cg_sketch_threshold` (Float, 0.1-1.0, default 0.5)
- `cg_sketch_min_line_length` (Int, 5-500, default 30)

### LLM 函数 API

已合并到 `dispatch_blender_job` 统一入口：

| functionName | 功能 | 关键参数 |
|---|---|---|
| `solve_point_layout` | 坐标点集 → 道路 mesh | `points` (必填), `connections` (可选), `mesh_name` |
| `extract_sketch_topology` | 草图图像 → 道路 mesh | `image_path` (必填), `method`, `threshold`, `min_line_length` |
| `clear_road_layout` | 删除当前道路布局 mesh | 无 |

### 成员 B 集成

```python
from bl_ext.user_default.LLMCityGenerator.dynamics.function_api import dispatch_blender_job

# 手动坐标
dispatch_blender_job("solve_point_layout", {
    "points": [[0,0],[50,0],[50,50],[0,50]]
})

# 草图提取
dispatch_blender_job("extract_sketch_topology", {
    "image_path": "C:/path/to/sketch.jpg",
    "threshold": 0.5,
    "min_line_length": 30
})
```

### 完整联调链（LLM 预期调用）

```
solve_point_layout({points: [...]})
  → cg.apply_node_group (Geo Nodes 生成城市)
  → run_full_simulation({car_density: 15})
  → 场景完成: 道路 + 建筑 + 车流 + 行人
```

## 注册流程

- `register()`: 注册类、定义 Scene 属性并注册帧变化处理器。
- `unregister()`: 反注册类、移除处理器并删除 Scene 属性。

## 开发工作流

### 插件打包与安装

由于 Blender 5.1 使用扩展系统，插件安装路径为：
```
C:\Users\<用户名>\AppData\Roaming\Blender Foundation\Blender\5.1\extensions\user_default\LLMCityGenerator\
```

开发时的工作流：
1. 在开发目录 `D:\Software Engineering\code\SE_26Spring\LLMCityGenerator\` 编辑代码
2. 将 `LLMCityGenerator/` 打包为 `.zip`（排除 `__pycache__`、`.git`、测试文件）
3. 在 Blender 中：`Edit > Preferences > Add-ons > Install from Disk` 安装 zip
4. 重启 Blender 或按 `F3` 搜索 `Reload Scripts` 重载

### 外部资产文件

`assets/pedestrians.blend` — 行人模型（来自 Procedural Crowds）。包含两个集合：
- `people`: 34 个角色 mesh 对象（静态 T-pose）
- `armatures`: 34 个骨骼对象（行人系统不使用，仅保留以维持模型结构）

插件启动时通过 `_resolve_pedestrian_collection()` 自动加载。

### Blender 控制台测试
```python
from bl_ext.user_default.LLMCityGenerator.dynamics.function_api import dispatch_blender_job
dispatch_blender_job("list_available_models")       # 查看可用模型
dispatch_blender_job("run_full_simulation", {})      # 启动仿真
dispatch_blender_job("get_simulation_status")        # 查看状态
dispatch_blender_job("stop_simulation")              # 停止
dispatch_blender_job("solve_point_layout", {"points": [[0,0],[50,0],[50,50],[0,50]]})
```

### 驱动方式（更新）
**纯 Python 驱动**：汽车、行人、交通灯全部由 `bpy.app.timers` 定时器驱动，不再依赖 Geo Nodes 仿真缓存。
- **汽车**：`CarManager` 在每条道路车道上生成车辆（linked duplicate），每帧更新位置/旋转
- **行人**：`PedestrianManager` 从 `assets/pedestrians.blend` 加载角色 mesh，linked duplicate 到人行道上，每帧移动
- **交通灯**：`TrafficLightManager` 在路口放置信号灯模型，timer 中切换状态
