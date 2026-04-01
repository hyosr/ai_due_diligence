from fastapi import Header, HTTPException
from app.core.config import settings

def require_api_key(x_api_key: str = Header(default="")):
    expected = getattr(settings, "api_key", "")
    if expected and x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")