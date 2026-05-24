# 智能城市生成系统前端原型

这是一个可独立运行的 React + TypeScript + Vite 前端骨架。当前阶段使用 mock 数据和本地状态模拟后端、Blender 插件、LLM 编排与仿真服务，所有业务请求统一经过 `src/services/api` 抽象层。

## 启动

```bash
npm install
npm run dev
```

默认访问：

```text
http://localhost:5173
```

## 账号

登录页提供三类演示账号：

- 场景建模师：`modeler@nku.city` / `demo1234`
- 行业分析师：`analyst@nku.city` / `demo1234`
- 系统管理员：`admin@nku.city` / `demo1234`

## 结构

- `src/services/api`：统一 API 门面与 mock 实现，未来替换这里即可接入真实后端。
- `src/types`：领域类型、DTO 与状态枚举。
- `src/context`：会话与业务数据上下文。
- `src/pages`：登录、工作台、项目场景、任务编排、多模态、仿真、审计版本、系统设置。
- `src/components`：布局、通用 UI 与业务可视化组件。

## 验证

```bash
npm run build
```
