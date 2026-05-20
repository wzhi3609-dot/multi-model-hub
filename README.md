# Multi-Model Hub

集成多个主流大模型，按照各自擅长的领域自动调度任务，支持手动切换和流式对话。

## 功能特性

- **多模型集成** — DeepSeek V3、Gemini 2.0 Flash、Groq (Llama 3.3 70B)
- **自动路由** — 根据任务类型智能选择最合适的模型
- **手动切换** — 可随时切换指定模型
- **流式输出** — SSE 实时返回，像 ChatGPT 一样逐字显示
- **多轮对话** — 完整上下文支持
- **历史记录** — SQLite 持久化存储，随时回顾
- **Markdown 渲染** — 代码高亮、表格、列表等

## 模型能力标签

| 模型 | 擅长领域 |
|------|---------|
| DeepSeek V3 | 编程、数学、推理、中文 |
| Gemini 2.0 Flash | 写作创作、翻译、创意 |
| Groq (Llama 3.3 70B) | 英文对话、快速推理 |

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API Key

复制 `.env.example` 为 `.env`，填入你的 API Key：

```bash
cp .env.example .env
```

获取免费 API Key:
- **DeepSeek**: https://platform.deepseek.com/api_keys
- **Gemini**: https://aistudio.google.com/apikey
- **Groq**: https://console.groq.com/keys

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
│   ├── config.py            # 配置 & 模型注册表
│   ├── schemas.py           # Pydantic 模型
│   ├── db/
│   │   ├── database.py      # SQLite 连接
│   │   └── models.py        # 数据访问层
│   ├── models/
│   │   ├── router.py        # 标签系统 & 自动路由
│   │   └── adapters/        # 模型适配器
│   │       ├── base.py
│   │       ├── deepseek.py
│   │       ├── gemini.py
│   │       └── groq.py
│   └── services/
│       ├── chat_service.py  # 对话编排
│       └── history_service.py
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── app.js
├── run.py
├── requirements.txt
├── .env.example
└── .gitignore
```

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| `GET` | `/api/models` | 可用模型列表 |
| `POST` | `/api/chat/send` | 发消息（SSE 流式） |
| `GET` | `/api/conversations` | 对话列表 |
| `POST` | `/api/conversations` | 新建对话 |
| `GET` | `/api/conversations/{id}` | 对话详情+消息 |
| `DELETE` | `/api/conversations/{id}` | 删除对话 |
| `PUT` | `/api/conversations/{id}` | 切换模型 |
| `POST` | `/api/route/suggest` | 路由建议 |
