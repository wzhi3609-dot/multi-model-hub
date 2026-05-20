import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
QWEN_BASE_URL = os.getenv("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8000))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "multi_model_hub.db")

MODEL_REGISTRY = {
    "groq": {
        "name": "Groq (Llama 3.3 70B)",
        "display_name": "Groq",
        "provider": "groq",
        "api_model": "llama-3.3-70b-versatile",
        "tags": ["english", "creative", "reasoning", "general"],
        "description": "速度快，擅长英文对话、创意写作",
        "enabled": bool(GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here"),
    },
    "mistral": {
        "name": "Mistral Saba 24B",
        "display_name": "Mistral",
        "provider": "groq",
        "api_model": "mistral-saba-24b",
        "tags": ["translation", "creative", "writing", "general"],
        "description": "擅长多语言翻译、创意写作",
        "enabled": bool(GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here"),
    },
    "qwen": {
        "name": "Qwen Turbo",
        "display_name": "千问",
        "provider": "qwen",
        "api_model": "qwen-turbo",
        "tags": ["chinese", "writing", "reasoning", "translation", "general"],
        "description": "中文理解力强，擅长写作、推理、翻译",
        "enabled": bool(QWEN_API_KEY and QWEN_API_KEY != "your_qwen_api_key_here"),
    },
    "qwen-coder": {
        "name": "Qwen 2.5 Coder 32B",
        "display_name": "千问Coder",
        "provider": "groq",
        "api_model": "qwen-2.5-coder-32b",
        "tags": ["coding", "math", "reasoning", "chinese", "english", "general"],
        "description": "专精编程、数学推理，中文英文兼优",
        "enabled": bool(GROQ_API_KEY and GROQ_API_KEY != "your_groq_api_key_here"),
    },
}

TAG_CONFIG = {
    "coding": {
        "name": "编程",
        "keywords": ["代码", "编程", "code", "函数", "function", "bug", "debug", "python", "java",
                      "写一个", "实现", "算法", "algorithm", "api", "sql", "数据库", "测试",
                      "重构", "refactor", "html", "css", "javascript", "后端", "前端"],
    },
    "math": {
        "name": "数学",
        "keywords": ["数学", "计算", "公式", "解方程", "math", "求导", "积分", "概率",
                      "统计", "几何", "代数"],
    },
    "reasoning": {
        "name": "推理",
        "keywords": ["推理", "分析", "为什么", "原因", "逻辑", "reasoning", "论证",
                      "思考", "判断", "结论"],
    },
    "chinese": {
        "name": "中文",
        "keywords": [],
    },
    "writing": {
        "name": "写作",
        "keywords": ["写文章", "写作", "创作", "故事", "小说", "文案", "写一篇", "文章",
                      "报告", "总结", "摘要", "博客", "blog", "write", "essay", "作文"],
    },
    "creative": {
        "name": "创意",
        "keywords": ["创意", "点子", "想法", "头脑风暴", "灵感", "brainstorm",
                      "设计", "方案"],
    },
    "translation": {
        "name": "翻译",
        "keywords": ["翻译", "translate", "英文", "中文翻译", "日文", "韩文",
                      "英译", "中译", "翻成"],
    },
    "english": {
        "name": "英文",
        "keywords": ["english", "essay", "article", "paragraph", "grammar"],
    },
    "general": {
        "name": "通用",
        "keywords": [],
    },
}
