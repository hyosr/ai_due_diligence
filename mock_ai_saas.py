from fastapi import FastAPI, Header, HTTPException
import random

app = FastAPI(title="Mock AI SaaS - Vulnerable Version")

# Simulate a weak API key (easily guessable)
VALID_API_KEY = "weak-key-123"

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/ai/generate")
async def generate_text(prompt: dict, x_api_key: str = Header(None)):
    if x_api_key != VALID_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Simulate insecure response (no rate limiting, no input sanitization)
    user_input = prompt.get("prompt", "")
    
    # Deliberately echo back user input (vulnerable to prompt injection)
    return {
        "generated_text": f"Echo: {user_input}",
        "model": "mock-ai-v1",
        "warning": "This service is for testing only"
    }

# Expose security headers missing (no CSP, no HSTS)
# Run with: uvicorn mock_ai_saas:app --port 8001