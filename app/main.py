from fastapi import FastAPI
from app.core.db import init_db
from app.api.intake import router as intake_router
from app.api.assessment import router as assessment_router
from app.api.report import router as report_router

from app.api.ui import router as ui_router

app = FastAPI(title="AI Due Diligence API", version="1.0.0")

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(intake_router)
app.include_router(assessment_router)
app.include_router(report_router)

app.include_router(ui_router)


@app.get("/")
def health():
    return {"status": "ok", "service": "ai-due-diligence"}