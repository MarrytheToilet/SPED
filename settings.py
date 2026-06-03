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

DEFAULT_COLLECTION = os.getenv("DEFAULT_COLLECTION", "人工关节材料摩擦学")

# Canonical data layout:
# data/collections/<collection>/{pdfs,parsed,schemas,extracted/<schema_slug>}
# data/state/pdf_state.db
COLLECTIONS_DIR = DATA_DIR / "collections"
STATE_DIR = DATA_DIR / "state"


def safe_collection_name(collection: str = "") -> str:
    raw = (collection or DEFAULT_COLLECTION).strip().replace("\\", "/").strip("/")
    parts = [p for p in raw.split("/") if p and p not in (".", "..")]
    return "/".join(parts) or DEFAULT_COLLECTION


def collection_root(collection: str = "") -> Path:
    return COLLECTIONS_DIR / safe_collection_name(collection)


def collection_pdf_dir(collection: str = "") -> Path:
    return collection_root(collection) / "pdfs"


def collection_parsed_dir(collection: str = "") -> Path:
    return collection_root(collection) / "parsed"


def collection_schema_dir(collection: str = "") -> Path:
    return collection_root(collection) / "schemas"


def collection_extracted_dir(collection: str = "", schema_slug: str = "") -> Path:
    root = collection_root(collection) / "extracted"
    return root / schema_slug if schema_slug else root


def logical_pdf_name(path: Path, collection: str = "") -> str:
    """Return Web/API-facing PDF name: <collection>/<relative-pdf-path>."""
    path = Path(path)
    coll = safe_collection_name(collection)
    try:
        rel = path.relative_to(collection_pdf_dir(coll))
        return str(Path(coll) / rel).replace("\\", "/")
    except ValueError:
        try:
            rel = path.relative_to(COLLECTIONS_DIR)
            parts = rel.parts
            if len(parts) >= 3 and parts[1] == "pdfs":
                return str(Path(parts[0], *parts[2:])).replace("\\", "/")
        except ValueError:
            pass
    return str(Path(coll) / path.name).replace("\\", "/")


def pdf_path_from_logical(name: str) -> Path:
    """Resolve <collection>/<relative-pdf-path> to canonical pdfs path."""
    rel = Path(str(name).replace("\\", "/").strip("/"))
    parts = rel.parts
    if not parts:
        return collection_pdf_dir(DEFAULT_COLLECTION)
    coll = safe_collection_name(parts[0])
    tail = Path(*parts[1:]) if len(parts) > 1 else Path("")
    return collection_pdf_dir(coll) / tail


# Backward-compatible constants. New code should use collection_* helpers.
RAW_DATA_DIR = DATA_DIR / "raw"
PDF_DIR = COLLECTIONS_DIR
PROCESSED_DIR = DATA_DIR / "processed"
PARSED_DIR = COLLECTIONS_DIR
EXTRACTED_DIR = COLLECTIONS_DIR
UPLOADS_DIR = STATE_DIR
SCHEMA_DIR = COLLECTIONS_DIR
GENERATED_SCHEMA_DIR = collection_schema_dir(DEFAULT_COLLECTION)
BATCH_CSV = UPLOADS_DIR / "upload_batches.csv"

# 确保目录存在
for dir_path in [
    COLLECTIONS_DIR,
    STATE_DIR,
    collection_pdf_dir(DEFAULT_COLLECTION),
    collection_parsed_dir(DEFAULT_COLLECTION),
    collection_schema_dir(DEFAULT_COLLECTION),
    collection_extracted_dir(DEFAULT_COLLECTION),
]:
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
# 单个 PDF 体积上限（MB）：超过则拒绝上传/解析（MinerU 对大文件易超时/失败）
MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "20"))
# 长时间停留在 uploaded 的 PDF 视为解析失败，避免永久显示处理中
PROCESSING_STALE_HOURS = int(os.getenv("PROCESSING_STALE_HOURS", "12"))
# MinerU 上传速率上限（文件/分钟）：官方限制约 50/min，超出会 HTTP 429
MINERU_UPLOAD_RATE_PER_MIN = int(os.getenv("MINERU_UPLOAD_RATE_PER_MIN", "50"))
BATCH_MAX_TOTAL_MB = int(os.getenv("BATCH_MAX_TOTAL_MB", "120"))
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
# ==========================
# 提取结果存储（已弃用固定12表数据库；改为 collection-local JSON + schema）
# ==========================
# 旧的 artificial_joint.db / 12表导入流程已移除。
# 提取结果以 JSON 落在 data/collections/<collection>/extracted/，
# schema 落在 data/collections/<collection>/schemas/。

# ==========================
# LLM API 配置（OpenAI 兼容端点 + 多agent分角色）
# ==========================
# 基础端点：只需 模型 / Base URL / API Key。
# 兼容任意 OpenAI 兼容服务（DeepSeek、Qwen、GLM、Kimi、OpenAI、SiliconFlow ...）。
LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")
LLM_API_BASE = os.getenv("LLM_API_BASE", os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"))
LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")  # 统一走 OpenAI 兼容客户端

# ---- 向后兼容别名 ----
DEFAULT_MODEL = LLM_MODEL

# ==========================
# 多agent分角色配置
# ==========================
# 每个角色可独立配置 模型/Base URL/API Key，未配置则回退到基础端点(LLM_*)。
# 环境变量命名：AGENT_<ROLE>_MODEL / AGENT_<ROLE>_API_BASE / AGENT_<ROLE>_API_KEY
# 设计意图：用「不同家族」的模型分别担任不同角色，靠多样性提升schema质量。
#
# 角色：
#   schema_agent_a/b/c —— schema 自动发现：每个 agent 独立阅读同一批样本并产出完整 schema
#   schema_merger       —— 合并多份 schema 草案
#   schema_reviewer     —— 审阅合并后的 schema
#   proposer_a/b/c / consolidator / critic —— 旧字段候选式 schema 流程角色（兼容保留）
#   extractor_a/b/c     —— 多路提取角色
#   extract_merger      —— 多路提取结果合并角色
#   extract_reviewer    —— 提取结果与 evidence 审阅角色
AGENT_ROLE_NAMES = [
    "schema_agent_a", "schema_agent_b", "schema_agent_c", "schema_merger", "schema_reviewer",
    "proposer_a", "proposer_b", "proposer_c", "consolidator", "critic",
    "extractor", "extractor_a", "extractor_b", "extractor_c", "extract_merger", "extract_reviewer",
]

# Schema 自动发现阶段：默认 3 个 agent 独立阅读同一批样本，各自产出完整 schema。
SCHEMA_AGENT_ROLES = [
    r.strip() for r in os.getenv("SCHEMA_AGENT_ROLES", "schema_agent_a,schema_agent_b,schema_agent_c").split(",") if r.strip()
]
SCHEMA_MERGER_ROLE = os.getenv("SCHEMA_MERGER_ROLE", "schema_merger").strip() or "schema_merger"
SCHEMA_REVIEWER_ROLE = os.getenv("SCHEMA_REVIEWER_ROLE", "schema_reviewer").strip() or "schema_reviewer"

# 旧候选式流程兼容项（默认不作为主流程使用）
SCHEMA_PROPOSER_ROLES = [
    r.strip() for r in os.getenv("SCHEMA_PROPOSER_ROLES", "proposer_a,proposer_b,proposer_c").split(",") if r.strip()
]
SCHEMA_PROPOSER_STRATEGY = os.getenv("SCHEMA_PROPOSER_STRATEGY", "all").strip().lower() or "all"

# 提取阶段默认 2 个 extractor + merger + reviewer。
EXTRACTOR_ROLES = [
    r.strip() for r in os.getenv("EXTRACTOR_ROLES", "extractor_a,extractor_b").split(",") if r.strip()
]
EXTRACT_MERGER_ROLE = os.getenv("EXTRACT_MERGER_ROLE", "extract_merger").strip() or "extract_merger"
EXTRACT_REVIEWER_ROLE = os.getenv("EXTRACT_REVIEWER_ROLE", "extract_reviewer").strip() or "extract_reviewer"
EXTRACT_REVIEW_ENABLED = os.getenv("EXTRACT_REVIEW_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}


def get_agent_config(role: str = None) -> dict:
    """
    获取某个agent角色的端点配置。

    优先读 AGENT_<ROLE>_*，缺省回退到基础 LLM_*。
    返回: {role, model, api_base, api_key, provider}
    """
    role = (role or "extractor").strip()
    up = role.upper()

    def _env(suffix, fallback):
        return os.getenv(f"AGENT_{up}_{suffix}", fallback)

    model = _env("MODEL", LLM_MODEL)
    api_base = _env("API_BASE", LLM_API_BASE)
    api_key = _env("API_KEY", LLM_API_KEY)
    provider = _env("PROVIDER", LLM_PROVIDER)
    return {
        "role": role,
        "model": model,
        "api_base": api_base,
        "api_key": api_key,
        "provider": provider,
    }


def get_model_config(model: str = None) -> dict:
    """获取基础端点配置（任意 model 名都用基础 LLM_API_BASE/KEY）。"""
    model = model or LLM_MODEL
    if not LLM_API_KEY:
        raise ValueError("LLM API 密钥未配置，请在 .env 中设置 LLM_API_KEY")
    return {
        "provider": LLM_PROVIDER,
        "api_key": LLM_API_KEY,
        "api_base": LLM_API_BASE,
        "model": model,
    }


def list_agent_endpoints() -> dict:
    """列出各角色实际生效的端点（用于诊断/菜单展示）。"""
    out = {}
    for r in AGENT_ROLE_NAMES:
        c = get_agent_config(r)
        out[r] = {
            "model": c["model"],
            "api_base": c["api_base"],
            "has_key": bool(c["api_key"]),
        }
    return out

# ==========================
# LLM 调用配置
# ==========================
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_TOP_P = float(os.getenv("LLM_TOP_P", "0.95"))
LLM_MAX_INFLIGHT = int(os.getenv("LLM_MAX_INFLIGHT", "8"))

# 模型最大输出 token 数。reasoning 模型(思考+正文)需要很大额度，默认拉满到 65536，
# 避免因 max_tokens 不足导致正文为空/被截断。base.call() 仍会在截断时自动加倍重试。
LLM_MAX_OUTPUT_TOKENS = int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "65536"))
MODEL_MAX_TOKENS = {LLM_MODEL: LLM_MAX_OUTPUT_TOKENS}

# ==========================
# Schema 自动设计配置
# ==========================
SCHEMA_MIN_FIELDS = int(os.getenv("SCHEMA_MIN_FIELDS", "20"))   # 字段数下限
SCHEMA_MAX_FIELDS = int(os.getenv("SCHEMA_MAX_FIELDS", "80"))   # 字段数上限（放宽，允许更多字段）
SCHEMA_SAMPLE_SIZE = int(os.getenv("SCHEMA_SAMPLE_SIZE", "8"))  # 设计schema时采样论文数
SCHEMA_EXCERPT_BUDGET = int(os.getenv("SCHEMA_EXCERPT_BUDGET", "16000"))  # 单篇摘录字符预算

# ==========================
# 并行处理配置
# ==========================
MAX_WORKERS = int(os.getenv("MAX_WORKERS", "4"))
WEB_PORT = int(os.getenv("WEB_PORT", "8000"))
DEFAULT_WORKERS = os.getenv("DEFAULT_WORKERS", None)
if DEFAULT_WORKERS is not None:
    DEFAULT_WORKERS = int(DEFAULT_WORKERS)

# ==========================
# 提取输入大小护栏
# ==========================
# 单篇论文送入LLM的最大字符数；0 表示不限制（始终送全文）。
EXTRACT_MAX_INPUT_CHARS = int(os.getenv("EXTRACT_MAX_INPUT_CHARS", "0"))

# 提取阶段并行度：同时处理多少篇论文（每个worker独立LLM客户端）。
EXTRACT_CONCURRENCY = int(os.getenv("EXTRACT_CONCURRENCY", "8"))

# ==========================
# 日志配置
# ==========================
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ==========================
# 下载配置
# ==========================
DOWNLOAD_RETRY = int(os.getenv("DOWNLOAD_RETRY", "2"))
DOWNLOAD_TIMEOUT = int(os.getenv("DOWNLOAD_TIMEOUT", "180"))
DOWNLOAD_CHUNK_SIZE = int(os.getenv("DOWNLOAD_CHUNK_SIZE", "8192"))
DOWNLOAD_RETRY_BACKOFF_BASE = float(os.getenv("DOWNLOAD_RETRY_BACKOFF_BASE", "1.8"))
DOWNLOAD_RETRY_BACKOFF_MAX = int(os.getenv("DOWNLOAD_RETRY_BACKOFF_MAX", "8"))

# 上传重试配置
UPLOAD_RETRY = int(os.getenv("UPLOAD_RETRY", "2"))
UPLOAD_RETRY_BACKOFF_BASE = float(os.getenv("UPLOAD_RETRY_BACKOFF_BASE", "1.8"))
UPLOAD_RETRY_BACKOFF_MAX = int(os.getenv("UPLOAD_RETRY_BACKOFF_MAX", "8"))

# ==========================
# HTTP 请求配置
# ==========================
HTTP_REQUEST_TIMEOUT = int(os.getenv("HTTP_REQUEST_TIMEOUT", "20"))

# LLM 请求与重试配置
_llm_call_timeout_raw = os.getenv("LLM_CALL_TIMEOUT", "").strip()
LLM_CALL_TIMEOUT = float(_llm_call_timeout_raw) if _llm_call_timeout_raw else None
_llm_full_mode_max_tokens_raw = os.getenv("LLM_FULL_MODE_MAX_TOKENS", "").strip()
LLM_FULL_MODE_MAX_TOKENS = int(_llm_full_mode_max_tokens_raw) if _llm_full_mode_max_tokens_raw else None
LLM_MAX_RETRIES = int(os.getenv("LLM_MAX_RETRIES", "3"))
LLM_RETRY_BACKOFF_BASE = float(os.getenv("LLM_RETRY_BACKOFF_BASE", "10"))
LLM_RETRY_BACKOFF_MAX = int(os.getenv("LLM_RETRY_BACKOFF_MAX", "120"))
LLM_RETRY_MAX_TOKENS_DECAY = float(os.getenv("LLM_RETRY_MAX_TOKENS_DECAY", "0.7"))

# 请求间隔配置（避免请求过于密集被ban）
LLM_MIN_INTERVAL = float(os.getenv("LLM_MIN_INTERVAL", "3.0"))

# SiliconFlow 推理开关（仅对支持的模型生效）
SILICONFLOW_ENABLE_THINKING = os.getenv("SILICONFLOW_ENABLE_THINKING", "False").lower() == "true"
SILICONFLOW_THINKING_BUDGET = int(os.getenv("SILICONFLOW_THINKING_BUDGET", "1024"))


# ==========================
# 运行时重载配置（供 Web 设置页热更新使用）
# ==========================
def reload_config() -> dict:
    """从 .env 重新加载并重算「可热更新」的端点配置。

    仅覆盖 Web 设置页可编辑的字段：MinerU(token/base) 与 LLM(model/base/key/provider)。
    LLM 工厂(_base_defaults)与 get_agent_config 在调用时读取这些模块全局量，
    因此重算后立即生效；MinerU 由 PDFProcessor 在构造时快照，重载只影响新建实例
    （避免打断进行中的解析任务）。
    返回当前生效的（脱敏后）配置摘要。
    """
    global DEFAULT_COLLECTION
    global MINERU_TOKEN, MINERU_API_BASE, MINERU_HEADERS
    global MAX_PDF_SIZE_MB, MINERU_UPLOAD_RATE_PER_MIN
    global LLM_MODEL, LLM_API_BASE, LLM_API_KEY, LLM_PROVIDER, DEFAULT_MODEL, LLM_MAX_INFLIGHT
    global EXTRACT_CONCURRENCY, PROCESSING_STALE_HOURS
    global SCHEMA_AGENT_ROLES, SCHEMA_MERGER_ROLE, SCHEMA_REVIEWER_ROLE
    global EXTRACTOR_ROLES, EXTRACT_MERGER_ROLE, EXTRACT_REVIEWER_ROLE, EXTRACT_REVIEW_ENABLED

    load_dotenv(override=True)

    DEFAULT_COLLECTION = os.getenv("DEFAULT_COLLECTION", DEFAULT_COLLECTION)
    MINERU_TOKEN = os.getenv("MINERU_TOKEN", "")
    MINERU_API_BASE = os.getenv("MINERU_API_BASE", "https://mineru.net/api/v4")
    MINERU_HEADERS = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {MINERU_TOKEN}",
    }

    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-v4-flash")
    LLM_API_BASE = os.getenv("LLM_API_BASE", os.getenv("OPENAI_API_BASE", "https://api.deepseek.com/v1"))
    LLM_API_KEY = os.getenv("LLM_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
    DEFAULT_MODEL = LLM_MODEL
    LLM_MAX_INFLIGHT = int(os.getenv("LLM_MAX_INFLIGHT", "8"))
    MAX_PDF_SIZE_MB = int(os.getenv("MAX_PDF_SIZE_MB", "20"))
    MINERU_UPLOAD_RATE_PER_MIN = int(os.getenv("MINERU_UPLOAD_RATE_PER_MIN", "50"))
    EXTRACT_CONCURRENCY = int(os.getenv("EXTRACT_CONCURRENCY", "8"))
    PROCESSING_STALE_HOURS = int(os.getenv("PROCESSING_STALE_HOURS", "12"))
    SCHEMA_AGENT_ROLES = [
        r.strip() for r in os.getenv("SCHEMA_AGENT_ROLES", "schema_agent_a,schema_agent_b,schema_agent_c").split(",") if r.strip()
    ]
    SCHEMA_MERGER_ROLE = os.getenv("SCHEMA_MERGER_ROLE", "schema_merger").strip() or "schema_merger"
    SCHEMA_REVIEWER_ROLE = os.getenv("SCHEMA_REVIEWER_ROLE", "schema_reviewer").strip() or "schema_reviewer"
    EXTRACTOR_ROLES = [
        r.strip() for r in os.getenv("EXTRACTOR_ROLES", "extractor_a,extractor_b").split(",") if r.strip()
    ]
    EXTRACT_MERGER_ROLE = os.getenv("EXTRACT_MERGER_ROLE", "extract_merger").strip() or "extract_merger"
    EXTRACT_REVIEWER_ROLE = os.getenv("EXTRACT_REVIEWER_ROLE", "extract_reviewer").strip() or "extract_reviewer"
    EXTRACT_REVIEW_ENABLED = os.getenv("EXTRACT_REVIEW_ENABLED", "true").strip().lower() not in {"0", "false", "no", "off"}

    return {"mineru_api_base": MINERU_API_BASE, "llm_model": LLM_MODEL,
            "llm_api_base": LLM_API_BASE, "extract_concurrency": EXTRACT_CONCURRENCY}
