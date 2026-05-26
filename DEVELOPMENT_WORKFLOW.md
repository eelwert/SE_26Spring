# 智能城市生成系统 - 团队开发流程

## 背景

当前代码库状况：Blender 插件 `LLMCityGenerator/__init__.py` 是一个 1600 行的单文件，所有 Operator、Panel、工具函数、属性注册全部混在一起，没有模块化拆分。前端 React 应用已初版完成，使用全量 mock 数据自运行。没有后端服务、没有测试、没有 CI 构建流程。四位成员需要在同一个代码库上并行开发六个功能方向。

核心风险：如果四人同时在 `__init__.py` 的同一个 1600 行单文件上开发，合并冲突将是灾难性的。必须首先完成插件模块化拆分，实现逻辑隔离后再启动各自的功能开发。

---

## Phase 0：基础设施搭建（全员协作，1-2天）

此阶段由指定一人主导，其余成员 Review。

### 0.1 插件模块化拆分

将 `LLMCityGenerator/__init__.py` 拆分为如下结构：

```
LLMCityGenerator/
├── __init__.py              # 仅保留 import + register/unregister + classes 列表
├── utils.py                 # append_data, get_or_create_attribute, find_layer_collection
├── operators/
│   ├── __init__.py
│   ├── import_apply.py      # CG_OT_Import_Node_Group, CG_OT_Apply_Node_Group, CG_OT_Duplicate_Object
│   └── mesh_attributes.py   # 所有 MESH_OT_* 属性赋值 Operator
├── panels/
│   ├── __init__.py
│   ├── main_panel.py        # CG_PT_Main_Panel, CG_Setting_Panel
│   ├── general_settings.py  # CG_General_Setting_Panel
│   ├── street_settings.py   # CG_Street_Setting_Panel, CG_Park_Setting_Panel, CG_Street_Adv_Setting_Panel
│   ├── building_settings.py # CG_Building_Panel 及其四个子面板
│   ├── traffic_sim.py       # CG_Traffic_Sim_Panel
│   └── night_lighting.py    # CG_Night_Lighting_Panel, InteriorPanel
├── properties.py            # Scene 属性注册/删除 + update 回调 + add_custom_properties 等
├── handlers.py              # frame_change_handler, update_parallax_settings
└── constants.py             # ADDON_DIR, BLEND_FILE 等常量 + Socket 编号映射字典
```

拆分原则：功能不变，仅做文件移动。拆分后立即在 Blender 中验证插件可正常加载、面板可正常显示、所有 Operator 可正常执行。

### 0.2 分支策略确定

```
main                          # 稳定版本
├── develop                   # 集成主干
│   ├── feature/assets        # 成员 A - 资产与模板
│   ├── feature/llm           # 成员 B - LLM 自然语言控制
│   ├── feature/eco-scene     # 成员 C - 生态化场景
│   └── feature/traffic       # 成员 D - 交通模拟与布局控制
```

每人从 `develop` 创建自己的 feature 分支。每天或每两天向 `develop` 合并一次（小步快跑，降低冲突）。合并前必须先 `git merge develop` 解决本地冲突。Phase 0 的模块化拆分在 `develop` 上完成，其他人从此拉取。

### 0.3 约定插件扩展规范

新增 Operator 在 `LLMCityGenerator/operators/` 下新建文件或追加到对应类别文件。新增 Panel 在 `LLMCityGenerator/panels/` 下新建文件，面板 `bl_parent_id` 统一挂在 `"CG_Setting_panel"` 下（或各自的子面板下）。新增 Scene 属性在 `properties.py` 中定义，同时在 `register()`/`unregister()` 中注册/删除。所有新类定义后添加到 `__init__.py` 的 `classes` 列表中。命名规范：Operator 为 `CG_OT_<snake_case_name>`，Panel 为 `CG_PT_<snake_case_name>`，`bl_idname` 为 `cg.<snake_case_name>`。

---

## Phase 1：各成员并行开发（2-3周）

### 成员 A：资产扩充 + 场景模板化（任务 4+5+6）

涉及文件：
- `LLMCityGenerator/panels/asset_panel.py`（新建：资产替换面板）
- `LLMCityGenerator/panels/template_panel.py`（新建：模板选择面板）
- `LLMCityGenerator/operators/asset_ops.py`（新建：资产加载/替换操作符）
- `LLMCityGenerator/properties.py`（追加：模板参数字典场景属性）
- `LLMCityGenerator/constants.py`（追加：纹理路径、模型路径常量）

开发步骤：

1. 2D 道路纹理：在 Path/Asset 设置面板中增加纹理下拉框 UI，绑定到 Geometry Nodes 中控制道路材质的 Socket 编号，实现选择不同纹理后自动切换道路材质。
2. 3D 城市家具：从 `City_Generator2.0.blend` 资源库中加载路灯/垃圾桶/长椅等模型（已有部分资产），通过 `bpy.ops.wm.append` 实例化到场景。在面板中暴露数量、间距参数，绑定到对应 Socket。
3. 模板配置：在面板中增加模板编号输入框（0-9），硬编码字典映射模板 ID 到树木类型/道路类型/座椅类型的三元组。执行时依次设置对应 Geometry Nodes Socket 值。

可参考的现有代码：`CG_Park_Setting_Panel` 的树木密度滑块（Socket 绑定的标准模式）；`CG_Street_Setting_Panel` 的道路宽度、车道数量滑块（参数输入 UI 模式）。

### 成员 B：LLM 自然语言控制（任务 7）

涉及文件：
- `LLMCityGenerator/panels/llm_panel.py`（新建：自然语言输入面板）
- `LLMCityGenerator/operators/llm_ops.py`（新建：LLM 调用 Operator）
- `LLMCityGenerator/llm_service.py`（新建：大模型 API 调用 + JSON 解析）
- `LLMCityGenerator/function_registry.py`（新建：可调用函数的注册表）
- 可选：`src/services/api/realApi.ts`（前端真实 API 客户端，如需对接前端）

开发步骤：

1. LLM API 调用：封装大模型 API（DeepSeek/智谱等），发送 System Prompt（描述可用的 Blender 操作函数）+ User Prompt（用户自然语言指令），返回函数调用 JSON。
2. 函数注册表：维护一个字典，将功能名称（如 `set_trees`、`change_weather`、`set_road_width`）映射到对应的插件内部执行函数。每个函数明确其参数 Schema。
3. 参数映射：解析 LLM 返回的 JSON，匹配到函数注册表中的函数，调用相应的 Blender 操作。实现函数链式调用支持（如"将场景变暗，切换到夜晚，开启路灯"）。
4. 插件 UI：在 City Generator 侧边栏新增 LLM 输入面板，包含文本输入框和执行按钮。

与成员 C/D 的对接：成员 B 的函数注册表需要成员 C 和 D 暴露各自功能的标准接口（函数名 + 参数 Schema），由各成员在开发时提供。

### 成员 C：生态化场景元素（任务 9）

涉及文件：
- `LLMCityGenerator/panels/eco_panel.py`（新建：生态元素面板）
- `LLMCityGenerator/operators/eco_ops.py`（新建：地形/湖泊/河流操作符）
- `LLMCityGenerator/properties.py`（追加：生态相关场景属性）
- `LLMCityGenerator/constants.py`（追加：生态元素默认参数常量）

开发步骤：

1. 山丘地形：创建 Grid 基础网格，添加 Subdivision Surface 修改器增加顶点密度。添加 Displace 修改器，使用 Noise 纹理（Cloud 类型）驱动位移。面板暴露参数：山丘高度（0-500m）、噪波缩放（0.1-5.0）、噪波细节（0-16）。可叠加多个 Displace 修改器获得更自然的地形细节。
2. 湖泊水面：创建圆形 Mesh Circle 或自定义形状的平面作为水面。使用 Principled BSDF 材质（Transmission=1.0, Roughness=0.0, IOR=1.33）。添加 Noise 纹理驱动 Normal 输入产生波纹效果。面板参数：水面大小、波纹强度、水面颜色。
3. 河流与船只：使用 Bezier Curve 定义河流路径，沿曲线挤出水面网格（使用 Curve to Mesh 或 Array + Curve 修改器）。船只对象添加 Follow Path 约束，绑定到河流曲线，通过 Animation Data 驱动。支持多条河流/船只。面板参数：河流宽度、流速（船只速度）、船只类型选择。

与现有代码的关系：这些是全新的 Operator 和 Panel，挂在 `CG_Setting_Panel` 下作为新的子面板。基本不修改现有代码，冲突风险最低。

### 成员 D：交通模拟 + 布局控制（任务 8+10）

涉及文件：
- `LLMCityGenerator/panels/traffic_control_panel.py`（新建或扩展）
- `LLMCityGenerator/panels/layout_panel.py`（新建：布局控制面板）
- `LLMCityGenerator/operators/traffic_ops.py`（新建：交通元素操作符）
- `LLMCityGenerator/operators/layout_ops.py`（新建：布局导入操作符）
- `LLMCityGenerator/sketch_processor.py`（新建：OpenCV 草图处理）

开发步骤：

1. 交通与人群模拟：在场景中添加汽车/行人模型，沿道路曲线绑定 Follow Path 约束。实现路径数组使多条车辆流线沿不同道路运动。红绿灯逻辑使用 Blender Driver 或帧回调函数控制车辆启停。面板参数：车辆密度、行人密度、速度范围、交通灯间隔。
2. 手动布局控制：面板输入框接收 X,Y 坐标点和连接关系（可用多行文本或 CSV 格式）。解析后创建对应的道路曲线（Bezier）。面板提供"预览布局"和"应用布局"两个执行按钮。
3. 草图布局提取：面板增加文件选择器（`bpy.props.StringProperty(subtype='FILE_PATH')`）加载草图图像。使用 OpenCV（cv2）进行边缘检测、Hough 线变换提取线段。将提取的线段转换为 Blender Bezier 曲线。面板参数：检测阈值、最小线段长度。

与成员 A 的关系：布局 Operator 生成的道路曲线需要能触发成员 A 的道路材质和家具实例化，需要约定接口（通过场景属性或命名规范传递）。

---

## Phase 2：后端控制平面实现（成员 B 主导，1周）

当前前端使用 mock 数据，需要一个真实的控制平面连接前端和 Blender 插件。

新建目录 `backend/`，包含以下文件：
- `server.py`（FastAPI/Flask 主应用）
- `routes/`（API 路由，对应前端 18 个 API 方法）
- `blender_client.py`（通过 Blender Python API 或 CLI 驱动插件操作）
- `llm_service.py`（LLM 调用封装）

实现策略：后端实现 `src/services/api/mockApi.ts` 中的 18 个方法对应的 REST API。响应格式统一使用 `ApiEnvelope<T>`（`{ traceId, data, message }`）。Blender 操作可通过 Blender 命令行模式（`blender --background --python script.py`）触发。前端切换时修改 `src/services/api/index.ts`，将 `mockApi` 替换为真实 HTTP 客户端。

---

## Phase 3：集成联调（全员，1周）

各模块功能在 Blender 中独立验证通过后，成员 B 的函数注册表汇总所有成员的可调用函数。然后进行前端+后端+插件全链路联调：从自然语言输入到 LLM 解析到后端调度到插件执行到场景更新。每个功能方向编写 1-2 个演示用例（模板切换、自然语言控制、生态元素生成、交通模拟、草图布局）。最后进行大场景下的生成速度和 LLM 响应延迟的性能优化。

---

## Phase 4：文档与交付（全员，2-3天）

各成员编写自己模块的功能说明和使用方法。更新 `INTERFACE.md` 补充新增的 Operator、Panel、Socket 映射。制作演示视频/截图。整理项目结题报告。

---

## 风险与应对

| 风险 | 应对 |
|------|------|
| 四人同时编辑同一文件导致合并冲突 | Phase 0 完成模块化拆分，每人编辑独立文件 |
| Blender API 不熟悉 | 每人先花半天研读现有 `__init__.py` 中同类功能的实现模式 |
| LLM API 调用不稳定 | 成员 B 先对接 API 确认可用性；其他成员函数注册表接口尽量简单 |
| Blender 环境不一致 | 统一使用 Blender 4.3.0，`.blend` 资源文件通过 Git LFS 同步 |
| 功能间接口不匹配 | Phase 2 启动时成员 B 发布插件函数注册规范文档，各成员按规范暴露接口 |

## 验证方式

由于没有自动化测试，采用手动验证清单：
- 插件在 Blender 4.3.0 中可正常启用，无报错
- 所有新增面板在 City Generator 侧边栏可见
- 各功能执行后场景发生预期变化（地形生成、水面出现、船只移动等）
- 前端 `npm run build` 通过，无 TypeScript 错误
- 后端启动后，前端可正常获取数据（替换 mock）
