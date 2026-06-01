# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是南开大学《软件工程》课程大作业，基于 Blender 插件 The City Generator 进行二次开发，加入 React 前端与 LLM 支持，构建"智能城市生成系统"。

## 常用命令

```bash
# 前端开发（端口 5173）
npm install
npm run dev          # 启动 Vite 开发服务器，--host 0.0.0.0
npm run build        # TypeScript 类型检查 + Vite 构建
npm run preview      # 预览构建产物，--host 0.0.0.0
npm run lint         # ESLint 检查
```

## 架构总览

```
React 前端 (src/)          后端控制平面 (尚未实现)        Blender 插件 (LLMCityGenerator/)
─────────────────────      ──────────────────────      ────────────────────────────────
pages/ ──→ context/ ──→ services/api/                   __init__.py      # 插件入口 + register/unregister
          WorkspaceContext   ├── index.ts  ← 统一门面   INTERFACE.md    # 插件完整接口文档（权威）
          SessionContext     ├── mockApi.ts ← 全量 mock   dynamics/       # 动态仿真（成员 D）
                             └── mockData.ts              layout/         # 道路布局（成员 D）
                        ↓                               operators/      # 操作符
                   types/domain.ts  ← 前端-后端类型契约   panels/         # UI 面板
                                                        City_Generator2.0.blend  # Geometry Nodes 资源库（Git LFS）
```

### 关键路径

- **插件入口**: `LLMCityGenerator/__init__.py` — `register()` 中调用 `register_class` → `register_scene_properties` → `register_handlers`
- **LLM 函数 API**: `LLMCityGenerator/dynamics/function_api.py` — `FUNCTION_REGISTRY` dict + `dispatch_blender_job()` 统一入口
- **接口文档**: `LLMCityGenerator/INTERFACE.md` — 所有 Operator / Panel / Socket 的权威文档，每次功能变更必须更新

## Blender 5.1 关键差异

当前开发环境是 **Blender 5.1**（不是 4.3）。关键差异：

- **扩展系统**: 插件安装路径变成 `extensions/user_default/`，Python 模块路径前缀为 `bl_ext.user_default`
- **导入方式**: 在 Blender 控制台中必须用 `from bl_ext.user_default.LLMCityGenerator.xxx import yyy`
- **`bpy.ops.wm.append`**: 上下文限制更严，`utils.py` 已改用 `bpy.data.libraries.load()` 替代
- **Vector 哈希**: `mathutils.Vector` 必须 `.freeze()` 后才能用作 dict key

## 插件注册模式

所有新增 Operator / Panel 必须：
1. 在对应 `operators/` 或 `panels/` 下新建或追加文件
2. 在 `operators/__init__.py` / `panels/__init__.py` 中导出
3. 在 `__init__.py` 的 `classes` 列表中注册
4. Panel 的 `bl_parent_id` 统一挂 `'CG_Setting_panel'`
5. 命名规范: Operator = `CG_OT_<snake>`, Panel = `CG_PT_<snake>`, `bl_idname` = `cg.<snake>`

## 成员 D 已实现功能（分支 `feature/path_dynamic_simulation`）

### dynamics/ 包 — 动态仿真系统

```
dynamics/
├── __init__.py               # 导出 + get_simulation_manager()
├── function_api.py            # ★ 12 个 LLM 可调用函数 + FUNCTION_REGISTRY + dispatch_blender_job
├── simulation_manager.py      # bpy.app.timers 驱动 → 行人和交通灯每帧更新
├── road_analyzer.py           # 网格边 → 双向车道 Bezier 曲线 + 路口转弯弧线
├── car_system.py              # 车辆模型加载 + place_on_curve() 静态工具
├── pedestrian_system.py       # 行人生成 + 人行道偏移曲线
└── traffic_light.py           # 路口检测 + 红绿灯放置（静态模型，无变色）
```

**混合架构**: 车辆运动由 Geo Nodes 原生仿真（Socket_89-109 配置 + Bake），Python 只驱动行人 + 交通灯。

### layout/ 包 — 道路布局控制

```
layout/
├── __init__.py
├── point_solver.py            # 坐标点集 → mesh（顶点=路口，边=道路）
├── sketch_processor.py        # 草图图像 → cv2/LLM → 线段 → mesh
└── layout_api.py              # LAYOUT_REGISTRY → 合并到 FUNCTION_REGISTRY
```

### 函数 API 模式

所有 LLM 可调用函数统一返回 `{"success": bool, "data": ..., "message": str}`。

成员 B 集成只需一行：
```python
from bl_ext.user_default.LLMCityGenerator.dynamics.function_api import FUNCTION_REGISTRY
# FUNCTION_REGISTRY 是 dict: {functionName: {function, description, params}}
```

后端调度器调用：
```python
dispatch_blender_job("run_full_simulation", {"car_density": 20})
# → {"success": True, "data": {...}, "message": "..."}
```

### 测试方法

在 Blender Python 控制台（`Shift+F11`）中：
```python
from bl_ext.user_default.LLMCityGenerator.dynamics.function_api import dispatch_blender_job
dispatch_blender_job("list_available_models", None)  # 查看 blend 文件中的集合
dispatch_blender_job("run_full_simulation", {...})    # 启动仿真
dispatch_blender_job("stop_simulation", None)         # 停止
dispatch_blender_job("solve_point_layout", {"points": [[0,0],[50,0],[50,50],[0,50]]})
```

## 前端-后端 API 契约

所有 API 响应统一包装为 `ApiEnvelope<T>`（`traceId` + `data` + 可选的 `message`）。任务执行通过 `functionName` 字段关联到 Blender 插件操作。前端目前使用全量 mock (`src/services/api/mockApi.ts`)。

## 小组分工与关键文件

当前分支: `feature/path_dynamic_simulation`

| 成员 | 任务 | 关键文件 |
|------|------|----------|
| 成员 A | 4+5+6 — 资产/模板 | `panels/asset_panel.py`, `operators/asset_ops.py` |
| 成员 B | 7 — LLM 控制 | `function_registry.py`（待建），需导入 `FUNCTION_REGISTRY` |
| 成员 C | 9 — 生态场景 | `panels/eco_panel.py`, `operators/eco_ops.py` |
| 成员 D | 8+10 — 交通/布局 | **`dynamics/function_api.py`**, **`layout/layout_api.py`** |

## 注意事项

- **插件扩展规范**: 新增 Scene 属性在 `properties.py` 中定义 + register/unregister
- **文档更新**: 每次功能变更必须同步更新 `INTERFACE.md`
- **Blender 5.1 路径**: 插件作为扩展安装，import 路径为 `bl_ext.user_default.LLMCityGenerator`
- **Git LFS**: `City_Generator2.0.blend` 和新增模型文件需 Git LFS 管理
- 不要修改 `src/types/domain.ts` 中的前端接口定义，如需变动需提供详细文档
