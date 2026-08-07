import hashlib
import secrets


API_KEY_PREFIX = "Aiml_agent"


def generate_api_key() -> str:
    tail = secrets.token_hex(24)
    return f"{API_KEY_PREFIX}{tail}"


def sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def api_key_prefix_display(full_key: str, visible: int = 16) -> str:
    if len(full_key) <= visible:
        return full_key
    return full_key[:visible] + "…"
