from fastapi import FastAPI
from app.core.db import init_db
from app.api.assessment import router as assessment_router
from app.api.report import router as report_router

app = FastAPI(title="AI Due Diligence – Zero Trust", version="3.0.0")


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(assessment_router)
app.include_router(report_router)


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-due-diligence-zero-trust"}