# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是南开大学《软件工程》课程大作业，基于 Blender 插件 The City Generator 进行二次开发，加入 React 前端与 LLM 支持，构建“智能城市生成系统”。

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
pages/ ──→ context/ ──→ services/api/                   __init__.py      # 插件主程序（~1600 行，基于 City Generator v2.8.0）
          WorkspaceContext   ├── index.ts  ← 统一门面   City_Generator2.0.blend  # Geometry Nodes 资源库（Git LFS）
          SessionContext     ├── mockApi.ts ← 全量 mock   INTERFACE.md    # 插件 UI/Socket 接口文档
                             └── mockData.ts
                        ↓
                   types/domain.ts  ← 前端-后端类型契约
```

当前阶段前端完全自包含，使用 `mockApi` 模拟所有后端行为。未来接入真实后端只需修改 `src/services/api/index.ts` 的导出。**团队约定：前端接口不应随意变动，如需变动必须提供详细文档说明。**

## 前端-后端 API 契约

所有 API 响应统一包装为 `ApiEnvelope<T>`（`traceId` + `data` + 可选的 `message`）。核心接口定义在 `src/services/api/mockApi.ts`（`MockSmartCityApi` 类）和 `src/types/domain.ts`。共 18 个方法，覆盖认证、工作区、项目管理、任务编排、多模态交互、仿真、版本快照、系统设置。详见 `src/services/api/mockApi.ts`。任务执行通过 `functionName` 字段关联到 Blender 插件操作（如 `dispatch_blender_job`、`replace_asset_batch`、`apply_template_linkage` 等）。

## Blender 插件关键信息

插件入口为 `LLMCityGenerator/__init__.py`，在 Blender 4.3.0 中作为 add-on 加载。UI 位于 View3D > Sidebar > City Generator。`INTERFACE.md` 记录了所有操作符、面板、场景属性和 ~80 个 Geometry Nodes Socket 绑定的完整接口。插件通过 Socket ID 控制 Geometry Nodes 修改器参数（道路宽度、建筑高度、树木密度、车道数量、路灯颜色等）。资源文件 `City_Generator2.0.blend` 使用 Git LFS 管理。

## 小组分工

当前分支 `feature/eco-scene`。

| 成员 | 任务 | 内容 |
|------|------|------|
| 成员 A | 任务 4+5+6 | 插件 UI 扩展、2D/3D 资产加载、场景模板化 |
| 成员 B | 任务 7 | LLM 自然语言控制（API 调用、NLP→JSON、参数映射） |
| 成员 C | **任务 9** | **生态化场景元素（当前开发者）**：山丘地形（位移修改器+噪波纹理）、湖泊水面（粒子系统/波纹材质）、河流与船只（路径动画） |
| 成员 D | 任务 8+10 | 交通与人群模拟、道路布局控制（手动坐标+OpenCV 草图提取） |

## 任务 9 开发要点（生态化场景元素）

开发在 `LLMCityGenerator/__init__.py` 中进行，通过 Blender 程序化生成实现：

1. **山丘地形**：使用 `bpy.ops.mesh.primitive_grid_add` 创建基础网格，添加 Displace 修改器配合 Noise 纹理生成起伏地形。暴露参数：山丘高度、噪波缩放、噪波细节。
2. **湖泊水面**：创建圆形/自由形状水面平面，使用 Principled BSDF 材质（Transmission≈1、Roughness≈0、Normal 贴图模拟波纹）。可配合粒子系统生成水花效果。
3. **河流与船只**：使用 Bezier 曲线定义河流路径，水面沿曲线延伸。船只作为子对象绑定到 Follow Path 约束，通过 `frame_current` 驱动实现动态行驶。

实现时遵循现有插件模式：定义 `bpy.types.Operator`（操作符）和 `bpy.types.Panel`（UI 面板），注册到 `View3D > Sidebar > City Generator` 面板层级中。
