import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "nvidia") # openai, anthropic, google, nvidia
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "AIzaSyCfZ01QfAAV7x91vrvPL2QTqgzWC3P4988")
    NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", "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")
    
    # Model parameters
    TEMPERATURE = float(os.getenv("TEMPERATURE", "0.1"))
    
    # Project Settings
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/tmp/mobile_security_workspace")

config = Config()
