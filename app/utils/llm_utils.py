from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_deepseek import ChatDeepSeek
from langchain_openai import ChatOpenAI # 导入 ChatOpenAI
import os
from dotenv import load_dotenv
from typing import Any

load_dotenv()

def get_llm_instance(model_provider: str = None) -> Any:
    """根据配置获取LLM模型实例"""
    model_provider = model_provider or os.getenv("LLM_MODEL", "gemini")

    if model_provider == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables.")
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
        return ChatGoogleGenerativeAI(model=gemini_model, api_key=api_key)
    elif model_provider == "deepseek":
        api_key = os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment variables.")
        deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat") # 从环境变量获取模型名称
        return ChatDeepSeek(model=deepseek_model, api_key=api_key)
    elif model_provider == "volces":
        api_key = os.getenv("VOLCES_API_KEY")
        base_url = os.getenv("VOLCES_BASE_URL")
        if not api_key or not base_url:
            raise ValueError("VOLCES_API_KEY or VOLCES_BASE_URL not found in environment variables for Volces model.")
        volces_model = os.getenv("VOLCES_MODEL", "volces-model-default") # 从环境变量获取模型名称
        # Volces兼容OpenAI协议，使用ChatOpenAI
        return ChatOpenAI(base_url=base_url, api_key=api_key, model_name=volces_model)
    else:
        raise ValueError(f"Unsupported LLM model provider: {model_provider}")