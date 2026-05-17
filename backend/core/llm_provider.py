from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.language_models.chat_models import BaseChatModel
from .config import config

def get_llm() -> BaseChatModel:
    """
    Returns the appropriate LLM instance based on configuration.
    """
    if config.LLM_PROVIDER == "openai":
        return ChatOpenAI(
            model="gpt-4o", 
            temperature=config.TEMPERATURE,
            api_key=config.OPENAI_API_KEY
        )
    elif config.LLM_PROVIDER == "anthropic":
        return ChatAnthropic(
            model="claude-3-5-sonnet-20240620", 
            temperature=config.TEMPERATURE,
            api_key=config.ANTHROPIC_API_KEY
        )
    elif config.LLM_PROVIDER == "google":
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-pro", 
            temperature=config.TEMPERATURE,
            api_key=config.GOOGLE_API_KEY
        )
    elif config.LLM_PROVIDER == "nvidia":
        return ChatOpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            model="google/gemma-3n-e4b-it",
            temperature=config.TEMPERATURE,
            api_key=config.NVIDIA_API_KEY
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {config.LLM_PROVIDER}")
