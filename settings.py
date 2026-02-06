"""
配置文件 - 统一管理所有配置
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# ==========================
# 项目路径配置
# ==========================
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SRC_DIR = BASE_DIR / "src"

# 数据目录
RAW_DATA_DIR = DATA_DIR / "raw"
PDF_DIR = RAW_DATA_DIR / "pdfs"
PROCESSED_DIR = DATA_DIR / "processed"
PARSED_DIR = PROCESSED_DIR / "parsed"
EXTRACTED_DIR = PROCESSED_DIR / "extracted"
ANALYZED_DIR = PROCESSED_DIR / "analyzed"
UPLOADS_DIR = DATA_DIR / "uploads"
SCHEMA_DIR = BASE_DIR / "data_schema"

# 确保目录存在
for dir_path in [PDF_DIR, PARSED_DIR, EXTRACTED_DIR, ANALYZED_DIR, UPLOADS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ==========================
# MinerU API 配置
# ==========================
MINERU_TOKEN = os.getenv("MINERU_TOKEN", "")
MINERU_API_BASE = os.getenv("MINERU_API_BASE", "https://mineru.net/api/v4")
MINERU_WEB_BASE = "https://mineru.net/extract/batch"

MINERU_HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {MINERU_TOKEN}"
}

# ==========================
# 上传配置
# ==========================
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "200"))
UPLOAD_CONFIG = {
    "enable_formula": os.getenv("UPLOAD_ENABLE_FORMULA", "True").lower() == "true",
    "language": os.getenv("UPLOAD_LANGUAGE", "en"),
    "layout_model": os.getenv("UPLOAD_LAYOUT_MODEL", "doclayout_yolo"),
    "enable_table": os.getenv("UPLOAD_ENABLE_TABLE", "True").lower() == "true",
}
FILE_CONFIG = {
    "parse_method": os.getenv("FILE_PARSE_METHOD", "auto"),
    "apply_ocr": os.getenv("FILE_APPLY_OCR", "False").lower() == "true",
}
BATCH_CSV = UPLOADS_DIR / "upload_batches.csv"

# ==========================
# 数据库配置
# ==========================
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "artificial_joint.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ==========================
# LLM API 配置
# ==========================
# 模型配置字典
AVAILABLE_MODELS = {
    # OpenAI
    "gpt-4o": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "api_base": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "api_base": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "api_base": os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1"),
    },
    # 硅基流动
    "Qwen/Qwen3-235B-A22B-Instruct-2507": {
        "provider": "siliconflow",
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "api_base": os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1"),
    },
    "moonshotai/Kimi-K2-Instruct-0905": {
        "provider": "siliconflow",
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "api_base": os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1"),
    },
    "Pro/moonshotai/Kimi-K2.5": {
        "provider": "siliconflow",
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "api_base": os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1"),
    },
    "Pro/zai-org/GLM-4.7": {
        "provider": "siliconflow",
        "api_key": os.getenv("SILICONFLOW_API_KEY", ""),
        "api_base": os.getenv("SILICONFLOW_API_BASE", "https://api.siliconflow.cn/v1"),
    },
    # DeepSeek
    "deepseek-chat": {
        "provider": "deepseek",
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
        "api_base": os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1"),
    },
    # 智谱AI
    "glm-4-plus": {
        "provider": "zhipu",
        "api_key": os.getenv("ZHIPU_API_KEY", ""),
        "api_base": os.getenv("ZHIPU_API_BASE", "https://open.bigmodel.cn/api/paas/v4"),
    },
    "glm-4-flash": {
        "provider": "zhipu",
        "api_key": os.getenv("ZHIPU_API_KEY", ""),
        "api_base": os.getenv("ZHIPU_API_BASE", "https://open.bigmodel.cn/api/paas/v4"),
    },
}

# 默认模型
DEFAULT_MODEL = os.getenv("LLM_MODEL", "moonshotai/Kimi-K2-Instruct-0905")

# 当前使用的模型配置
if DEFAULT_MODEL in AVAILABLE_MODELS:
    current_model_config = AVAILABLE_MODELS[DEFAULT_MODEL]
    OPENAI_API_KEY = current_model_config["api_key"]
    OPENAI_API_BASE = current_model_config["api_base"]
    OPENAI_MODEL = DEFAULT_MODEL
    LLM_PROVIDER = current_model_config["provider"]
else:
    print(f"⚠️  警告: 模型 '{DEFAULT_MODEL}' 不在预定义列表中，使用环境变量配置")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_MODEL = DEFAULT_MODEL
    LLM_PROVIDER = "custom"

# ==========================
# 动态配置函数
# ==========================

def get_model_config(model: str) -> dict:
    """
    获取指定模型的配置
    
    Args:
        model: 模型名称，如 'gpt-4o', 'Qwen/Qwen2.5-72B-Instruct' 等
    
    Returns:
        dict: 包含 provider, api_key, api_base, model 的配置字典
    
    Raises:
        ValueError: 如果模型不存在或API密钥未配置
    """
    if model not in AVAILABLE_MODELS:
        available = list(AVAILABLE_MODELS.keys())
        raise ValueError(
            f"未知的模型 '{model}'。\n"
            f"可用模型: {', '.join(available[:5])}... "
            f"(共{len(available)}个，使用 --list-models 查看全部)"
        )
    
    config = AVAILABLE_MODELS[model]
    
    # 检查API key是否配置
    if not config["api_key"]:
        # 根据provider给出提示
        provider = config.get("provider", "").upper()
        env_var = f"{provider}_API_KEY" if provider else "API_KEY"
        raise ValueError(
            f"模型 '{model}' 的API密钥未配置，"
            f"请在 .env 文件中设置 {env_var}"
        )
    
    return {
        "provider": config["provider"],
        "api_key": config["api_key"],
        "api_base": config["api_base"],
        "model": model,
    }


def list_available_models() -> dict:
    """
    列出所有可用的模型及其配置状态
    
    Returns:
        dict: {model: {provider, has_key, api_base}}
    """
    result = {}
    for model, config in AVAILABLE_MODELS.items():
        result[model] = {
            "provider": config["provider"],
            "has_key": bool(config["api_key"]),
            "api_base": config["api_base"],
        }
    return result

# ==========================
# LLM 调用配置
# ==========================
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.95"))
LLM_FREQUENCY_PENALTY = float(os.getenv("LLM_FREQUENCY_PENALTY", "0.0"))
LLM_PRESENCE_PENALTY = float(os.getenv("LLM_PRESENCE_PENALTY", "0.0"))

# 模型的max_tokens限制配置
MODEL_MAX_TOKENS = {
    "gpt-4o": int(os.getenv("GPT4O_MAX_TOKENS", "16000")),
    "gpt-4o-mini": int(os.getenv("GPT4O_MINI_MAX_TOKENS", "16000")),
    "gpt-4-turbo": int(os.getenv("GPT4_TURBO_MAX_TOKENS", "16000")),
    "Qwen/Qwen2.5-72B-Instruct": int(os.getenv("QWEN_72B_MAX_TOKENS", "30000")),
    "Qwen/Qwen2.5-7B-Instruct": int(os.getenv("QWEN_7B_MAX_TOKENS", "30000")),
    "moonshotai/Kimi-K2-Instruct-0905": int(os.getenv("KIMI_MAX_TOKENS", "32000")),
    "Pro/moonshotai/Kimi-K2-Instruct-0905": int(os.getenv("KIMI_MAX_TOKENS", "32000")),
    "deepseek-ai/DeepSeek-V2.5": int(os.getenv("DEEPSEEK_V25_MAX_TOKENS", "30000")),
    "deepseek-chat": int(os.getenv("DEEPSEEK_CHAT_MAX_TOKENS", "16000")),
    "glm-4-plus": int(os.getenv("GLM4_PLUS_MAX_TOKENS", "16000")),
    "glm-4-flash": int(os.getenv("GLM4_FLASH_MAX_TOKENS", "16000")),
}

# Chunk模式的max_tokens限制（通常小于full模式）
CHUNK_MODE_MAX_TOKENS = int(os.getenv("CHUNK_MODE_MAX_TOKENS", "4096"))

# ==========================
# 并行处理配置
# ==========================
# 最大worker数量（默认为CPU核心数，但不超过此值）
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
# 默认worker数量（None表示自动，将使用min(CPU核心数, MAX_WORKERS)）
DEFAULT_WORKERS = os.getenv("DEFAULT_WORKERS", None)
if DEFAULT_WORKERS is not None:
    DEFAULT_WORKERS = int(DEFAULT_WORKERS)

# ==========================
# 文本分块配置
# ==========================
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "10000"))  # 每个chunk的字符数
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "300"))  # chunk之间的重叠字符数

# ==========================
# 向量数据库配置
# ==========================
CHROMA_PERSIST_DIR = str(DATA_DIR / "chroma_db")

# ==========================
# 日志配置
# ==========================
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==========================
# 下载配置
# ==========================
DOWNLOAD_RETRY = int(os.getenv("DOWNLOAD_RETRY", "3"))
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "300"))
DOWNLOAD_CHUNK_SIZE = int(os.getenv("DOWNLOAD_CHUNK_SIZE", "8192"))

# ==========================
# HTTP 请求配置
# ==========================
HTTP_REQUEST_TIMEOUT = int(os.getenv("HTTP_REQUEST_TIMEOUT", "30"))
