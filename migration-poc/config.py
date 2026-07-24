"""Configuration for multi-agent extraction pipeline"""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
MODEL = os.getenv("MODEL", "deepseek/deepseek-chat")

# Extraction Configuration
TARGET_FRAMEWORK = os.getenv("TARGET_FRAMEWORK", "net10.0")
COMPLIANCE_CONTEXT = os.getenv("COMPLIANCE_CONTEXT", "21 CFR Part 11")
DOMAIN = os.getenv("DOMAIN", "medical/chromatography")

# OpenRouter Model Options
AVAILABLE_MODELS = {
    "deepseek": "deepseek/deepseek-chat",  # Fast, cheap, excellent code
    "llama": "meta-llama/llama-3.1-405b-instruct",  # Powerful but pricier
    "qwen": "qwen/qwen-2.5-72b-instruct",  # Good balance
}

# Output paths
OUTPUT_DIR = "output"
LEGACY_CODE_DIR = "legacy-code"
