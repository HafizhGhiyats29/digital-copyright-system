import os
from pathlib import Path
from typing import Optional

from fastapi import Header, HTTPException, status

INTERNAL_API_KEY_HEADER = "X-Internal-API-Key"
BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BASE_DIR.parent


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.lstrip("\ufeff").strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key and key not in os.environ:
            os.environ[key] = value


_load_env_file(PROJECT_ROOT / ".env")
_load_env_file(BASE_DIR / ".env")


def get_internal_api_key() -> str:
    return os.getenv("INTERNAL_API_KEY", "")


def internal_auth_headers() -> dict[str, str]:
    api_key = get_internal_api_key()
    return {INTERNAL_API_KEY_HEADER: api_key} if api_key else {}


def require_internal_api_key(
    x_internal_api_key: Optional[str] = Header(default=None, alias=INTERNAL_API_KEY_HEADER),
) -> None:
    expected = get_internal_api_key()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal API key is not configured",
        )

    if x_internal_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid internal API key",
        )
