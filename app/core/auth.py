from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader
from app.core.config import settings

api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

def require_api_key(api_key: str = Security(api_key_header)):
    expected = settings.api_key or ""
    # Si api_key n'est pas configurée => pas de protection (mode dev)
    if expected == "":
        return True
    if api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True