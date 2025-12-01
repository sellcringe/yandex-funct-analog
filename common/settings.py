import os
from dotenv import load_dotenv

load_dotenv()

def _as_bool(v, default=False):
    if v is None: return default
    return str(v).lower() in {"1","true","yes","y","on"}

class Settings:
    APP_ENV = os.getenv("APP_ENV", "prod")
    APP_LOG_LEVEL = os.getenv("APP_LOG_LEVEL", "INFO")
    APP_HTTP_TOKEN = os.getenv("APP_HTTP_TOKEN", "")

    ASPRO_API_KEY = os.getenv("ASPRO_API_KEY", "")
    ASPRO_BASE = os.getenv("ASPRO_BASE", "")

    CH_HOST = os.getenv("CH_HOST", "")
    CH_PORT = int(os.getenv("CH_PORT", "9440"))
    CH_USER = os.getenv("CH_USER", "")
    CH_PASSWORD = os.getenv("CH_PASSWORD", "")
    CH_SECURE = _as_bool(os.getenv("CH_SECURE", "true"), True)
    CH_VERIFY = _as_bool(os.getenv("CH_VERIFY", "true"), True)
    CH_CA_CERT = os.getenv("CH_CA_CERT", "")

settings = Settings()
