import os


def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


HOST = os.getenv("HOST", "127.0.0.1")
TEXT_PORT = int(os.getenv("TEXT_PORT", "8081"))
VISION_PORT = int(os.getenv("VISION_PORT", "8083"))
RELOAD = _env_bool("RELOAD", True)
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
