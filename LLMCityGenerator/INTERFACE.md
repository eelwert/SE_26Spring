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

## 注册流程

- `register()`: 注册类、定义 Scene 属性并注册帧变化处理器。
- `unregister()`: 反注册类、移除处理器并删除 Scene 属性。
