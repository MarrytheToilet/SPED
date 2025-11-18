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
BASE_DIR = Path(__file__).parent  # settings.py现在在项目根目录
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

# Schema目录
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

# 上传配置（从环境变量读取，提供默认值）
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

# 批次记录文件
BATCH_CSV = UPLOADS_DIR / "upload_batches.csv"

# ==========================
# 数据库配置 (SQLite)
# ==========================
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "artificial_joint.db"))
DATABASE_URL = f"sqlite:///{DB_PATH}"

# ==========================
# OpenAI API 配置
# ==========================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.zmon.me/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")
OPENAI_EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")

# ==========================
# Agent 配置
# ==========================
AGENT_CONFIG = {
    "max_iterations": int(os.getenv("AGENT_MAX_ITERATIONS", "5")),
    "temperature": float(os.getenv("AGENT_TEMPERATURE", "0.1")),
    "max_tokens": int(os.getenv("AGENT_MAX_TOKENS", "4000")),
    "enable_memory": os.getenv("AGENT_ENABLE_MEMORY", "True").lower() == "true",
}

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
