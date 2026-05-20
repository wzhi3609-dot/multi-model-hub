# Multi-Model Hub

集成多个主流大模型，按照各自擅长的领域自动调度任务，支持手动切换和流式对话。**所有模型均永久免费。**

## 功能特性

- **多模型集成** — Groq Llama 3.3、Mistral Saba、千问 Turbo、千问 Coder
- **自动路由** — 根据任务类型智能选择最合适的模型
- **手动切换** — 可随时切换指定模型
- **流式输出** — SSE 实时返回逐字显示
- **多轮对话** — 完整上下文支持
- **历史记录** — SQLite 持久化存储
- **Markdown 渲染** — 代码高亮、表格、列表

## 模型能力标签

| 模型 | 平台 | 擅长领域 |
|------|------|---------|
| Groq (Llama 3.3 70B) | Groq | 英文对话、推理、创意 |
| Mistral Saba 24B | Groq | 多语言翻译、写作 |
| 千问 Turbo | DashScope | 中文理解、写作、翻译 |
| 千问 Coder 2.5 32B | Groq | 编程、数学推理、中英文 |

### 自动路由关键词

| 标签 | 触发关键词 |
|------|-----------|
| 编程 | 代码、Python、bug、算法、API、SQL、重构... |
| 翻译 | 翻译、translate、英文、英译... |
| 写作 | 写文章、创作、故事、报告、博客、essay... |
| 数学 | 数学、计算、公式、概率、统计... |
| 推理 | 推理、分析、为什么、逻辑、判断... |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

```bash
copy .env.example .env
```

编辑 `.env`，填入 API Key：

```ini
# Groq — 支持 Llama 3.3 / Mistral / Qwen Coder
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxx

# Qwen Turbo
QWEN_API_KEY=sk-xxxxxxxxxxxxxxxxxx
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

获取免费 Key：

| 平台 | 地址 |
|------|------|
| Groq | https://console.groq.com/keys |
| DashScope | https://dashscope.console.aliyun.com/apiKey |

### 3. 启动

```bash
python run.py
```

浏览器打开 `http://localhost:8000`

## 项目结构

```
multi-model-hub/
├── backend/
│   ├── main.py              # FastAPI 入口 + 路由
│   ├── config.py            # 环境变量 + 模型注册表 + 标签关键词
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── db/
│   │   ├── database.py      # SQLite 连接 & 建表
│   │   └── models.py        # 数据访问层 (CRUD)
│   ├── models/
│   │   ├── router.py        # 标签系统 & 自动路由
│   │   └── adapters/
│   │       ├── base.py      # 抽象基类
│   │       ├── groq.py      # Groq / Mistral / Qwen Coder
│   │       └── qwen.py      # 千问 Turbo
│   └── services/
│       ├── chat_service.py  # 对话编排 (SSE 流式)
│       └── history_service.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js               # SSE 流式接收 + Markdown 渲染
├── run.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/models` | 可用模型列表及标签 |
| `POST` | `/api/chat/send` | 发消息（SSE 流式响应） |
| `GET` | `/api/conversations` | 对话列表 |
| `POST` | `/api/conversations` | 新建对话 |
| `GET` | `/api/conversations/{id}` | 对话详情 + 消息记录 |
| `DELETE` | `/api/conversations/{id}` | 删除对话 |
| `PUT` | `/api/conversations/{id}` | 切换模型 |
| `POST` | `/api/route/suggest` | 手动触发路由建议 |
