# 智药云数 (MedAgentMatrix)

## 项目简介

智药云数是一个基于多智能体大语言模型的商品主数据运营平台，专注于医药行业的商品信息自动化处理。该平台旨在通过AI技术，自动完成商品的分类、关键信息提取、数据验证、去重匹配，并对不确定项进行人工审核，从而高效、准确地构建和维护高质量的商品主数据。

本项目利用 `LangGraph` 构建核心的多智能体（Multi-Agent）工作流，结合 `FastAPI` 提供API服务，`SQLite` 作为开发数据库，`ChromaDB` 作为向量数据库（计划中），并支持接入多种大语言模型（如 Google Gemini, DeepSeek）。

## 核心功能

1.  **智能分类 (Classifier Agent)**: 自动识别输入文本对应的商品类型（药品、器械、药妆、保健品、中药饮片、普通商品）。
2.  **信息提取 (Extractor Agents)**: 针对不同商品类型，调用专门的Agent和Prompt，精确提取结构化信息。
3.  **数据验证 (Validator Agent)**: 对提取的信息进行规则校验，并通过模拟工具（未来替换为真实API）验证关键字段（如批准文号）的有效性。
4.  **去重匹配 (Matcher Agent)**: 检查提取的商品信息是否已在主数据中存在，避免重复录入。
5.  **人工审核 (Human-in-the-loop)**: 将验证失败或无法匹配的数据推送到审核队列，等待人工确认。
6.  **数据持久化**: 审核通过的数据将被保存到主商品数据表中。

## 技术架构

*   **后端语言**: Python 3.11+
*   **AI框架**: LangGraph, LangChain
*   **Web框架**: FastAPI
*   **数据库**:
    *   关系型数据库 (开发): SQLite
    *   关系型数据库 (生产): MySQL (计划中)
*   **向量数据库**:
    *   开发: ChromaDB
    *   生产: Milvus (计划中)
*   **LLM支持**:
    *   Google Gemini
    *   DeepSeek
*   **实时通信**: Socket.IO

## 项目结构

```
.
├── app/                  # 后端应用代码
│   ├── agents/           # 智能体 (LangGraph Nodes)
│   │   ├── classifier_agent.py
│   │   ├── drug_extractor_agent.py
│   │   ├── device_extractor_agent.py
│   │   ├── cosmeceutical_extractor_agent.py
│   │   ├── supplement_extractor_agent.py
│   │   ├── tcm_extractor_agent.py
│   │   ├── general_extractor_agent.py
│   │   ├── validator_agent.py
│   │   ├── matcher_agent.py
│   │   ├── human_in_the_loop_agent.py
│   │   └── save_product_agent.py
│   ├── api/              # FastAPI 路由
│   │   └── products.py
│   ├── models/           # 数据库模型 (SQLAlchemy)
│   │   └── schema.py
│   ├── services/         # 业务逻辑服务
│   │   └── product_service.py
│   ├── tools/            # 外部工具封装 (模拟NMPA查询)
│   │   └── nmpa_tool.py
│   ├── utils/            # 工具函数
│   ├── database.py       # 数据库连接与初始化
│   └── socket.py         # Socket.IO 配置
├── frontend/             # 前端代码 (待开发)
├── tests/                # 测试代码
├── main.py               # FastAPI 应用入口
├── requirements.txt      # Python 依赖
├── .env                  # 环境变量配置文件
├── .gitignore
└── README.md             # 本文件
```

## 运行方式

### 环境准备

1.  **Python版本**: 确保已安装 Python 3.11 或更高版本。
2.  **虚拟环境 (推荐)**:
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # macOS/Linux
    # source .venv/bin/activate
    ```
3.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

### 配置环境变量

在项目根目录下创建 `.env` 文件，并填入必要的配置信息：

```
# 选择默认的LLM模型 (gemini 或 deepseek)
LLM_MODEL=gemini

# Google Gemini 配置 (如果 LLM_MODEL=gemini)
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-2.0-flash # 可选，默认为 gemini-2.0-flash

# DeepSeek 配置 (如果 LLM_MODEL=deepseek)
DEEPSEEK_API_KEY=your_deepseek_api_key

# 数据库配置 (可选，默认使用 SQLite test.db)
# DATABASE_URL=sqlite:///./test.db
```

### 启动服务

在项目根目录下运行：

```bash
uvicorn main:app --reload
```

这将启动 FastAPI 开发服务器，默认地址为 `http://localhost:8000`。

你可以访问 `http://localhost:8000/docs` 查看自动生成的 API 文档。

### 测试API

你可以使用 `curl` 或 `test.http` 文件（如果您的编辑器支持）来测试API。

**示例：处理商品信息**

```http
POST http://localhost:8000/api/products/process
Content-Type: application/json

{
  "raw_text": "国药准字H20240001 蒙脱石散 3g*10袋/盒 湖北午时药业股份有限公司"
}
```

**示例：查询任务状态**

```http
GET http://localhost:8000/api/products/status/{task_id_from_previous_response}
```

**示例：获取待审核队列**

```http
GET http://localhost:8000/api/products/review/queue
```

**示例：提交审核结果**

```http
POST http://localhost:8000/api/products/review/submit/1
Content-Type: application/json

{
  "approved": true
}
```

