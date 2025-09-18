# 智药云数 (IntelliPharma-MDM) - 前端

## 项目简介

这是智药云数平台的前端用户界面，基于 React、TypeScript 和 Vite 构建。它提供了一个交互式的Web界面，用于提交商品信息、实时可视化多智能体处理流程、查看处理详情以及执行人工审核操作。

## 技术栈

*   **核心框架**: React 19
*   **语言**: TypeScript
*   **构建工具**: Vite
*   **UI库**: React Bootstrap (基于 Bootstrap 5)
*   **流程图库**: React Flow
*   **实时通信**: Socket.IO Client
*   **包管理**: npm (或 yarn, pnpm)

## 项目结构

```
frontend/
├── public/              # 静态资源文件
├── src/                 # 源代码目录
│   ├── assets/          # 本地静态资源 (图片, 字体等)
│   ├── App.css          # App组件局部样式
│   ├── App.tsx          # 主应用组件
│   ├── index.css        # 全局样式
│   ├── main.tsx         # 应用入口文件
│   └── vite-env.d.ts    # Vite TypeScript 类型声明
├── index.html           # 主页面模板
├── package.json         # 项目依赖和脚本
├── tsconfig.json        # TypeScript 配置 (基础)
├── tsconfig.app.json    # TypeScript 配置 (应用)
├── tsconfig.node.json   # TypeScript 配置 (Node工具)
├── vite.config.ts       # Vite 配置文件
└── README.md            # 本文件
```

## 核心功能与界面

1.  **商品信息提交**:
    *   在左侧的 "提交新商品" 卡片中，用户可以粘贴原始的商品描述文本。
    *   点击 "提交" 按钮，前端会通过Socket.IO将用户的Socket ID一并发送给后端API (`/api/products/process`)，以便后端能够实时推送处理状态。

2.  **处理流程可视化 (React Flow)**:
    *   中间的画布区域使用 React Flow 展示了整个 LangGraph 工作流。
    *   节点代表不同的 Agent (如商品分类、药品提取、数据验证等)。
    *   边代表 Agent 之间的流转关系。
    *   **状态指示**:
        *   **蓝色高亮边框**: 表示当前正在执行的 Agent。
        *   **绿色节点**: 表示已成功执行的 Agent。
        *   **红色节点**: 表示在验证阶段失败的 Agent (例如，数据验证未通过)。
        *   **黄色节点**: 表示需要人工审核的节点。
        *   **蓝色流动动画**: 表示已执行或正在执行的流程边。

3.  **任务状态与历史**:
    *   左上角的 "任务状态" 卡片显示当前任务的ID和处理状态 (如 "处理中...", "需要人工审核", "处理完成")。
    *   右侧下方的 "处理历史" 列表记录了所有已执行的步骤。

4.  **节点详情查看**:
    *   点击流程图中的任意节点，或点击 "处理历史" 列表中的条目，可以在右侧上方的 "节点详情" 卡片中查看该步骤的详细输入输出数据。

5.  **人工审核**:
    *   当流程到达 "人工审核" 节点时，右侧上方会弹出一个 "人工审核" 卡片。
    *   卡片中会显示审核原因和审核项ID。
    *   用户可以选择 "批准" 或 "拒绝"。
    *   **批准**: 后端将继续执行保存商品的流程。
    *   **拒绝**: 当前任务流程结束。

## 运行方式

### 环境准备

1.  **Node.js**: 确保已安装 Node.js LTS 版本 (推荐 18.x 或 20.x)。
2.  **包管理器**: 项目默认使用 `npm`。如果习惯使用 `yarn` 或 `pnpm`，请相应调整命令。

### 安装依赖

在 `frontend` 目录下执行:

```bash
npm install
```

### 开发环境启动

在 `frontend` 目录下执行:

```bash
npm run dev
```

这将启动 Vite 开发服务器，默认地址为 `http://localhost:5173`。Vite 提供了热模块替换 (HMR) 功能，代码修改后会自动刷新浏览器。

**注意**: 前端开发服务器默认配置为代理 `/api` 请求到后端服务 `http://localhost:8000` (在 `vite.config.ts` 中配置)。请确保后端服务已在运行。

### 构建生产版本

在 `frontend` 目录下执行:

```bash
npm run build
```

构建后的静态文件将输出到 `frontend/dist` 目录。这些文件可以部署到任何静态文件服务器上。

### 预览生产构建

在 `frontend` 目录下执行:

```bash
# 首先确保已经构建
npm run build
# 然后预览
npm run preview
```

这将在本地启动一个静态服务器来预览构建后的版本。

## 代码简析 (App.tsx)

*   **Socket.IO 集成**: 使用 `socket.io-client` 连接到后端，并监听 `agent_step` 事件来接收实时更新。
*   **React Flow**: 使用 `useNodesState` 和 `useEdgesState` hooks 来管理流程图的状态。节点和边的样式根据任务历史和当前状态动态更新。
*   **状态管理**: 使用 React 的 `useState` 和 `useEffect` hooks 来管理组件内部状态，如用户输入、任务历史、当前选中节点详情等。
*   **API 调用**: 使用 `fetch` API 与后端进行交互，包括提交任务和提交审核结果。

## 开发与扩展

*   **UI 样式**: 基于 React Bootstrap 和 Bootstrap CSS，易于进行主题定制和响应式布局。
*   **流程图**: React Flow 提供了强大的自定义能力，可以方便地扩展节点类型、添加交互等。
*   **类型安全**: TypeScript 为整个项目提供了类型安全保障，提高了代码可维护性。