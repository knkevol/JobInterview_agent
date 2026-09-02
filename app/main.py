# FastAPI 앱의 진입점.
# 실제 엔드포인트는 include_router로 연결

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app import interview_routes
from app.db import init_db
from app.quiz import quiz_routes
from app.quiz.logic import seed_quiz_bank


app = FastAPI(title="AI Interviewer Agent")

app.include_router(quiz_routes.router)
app.include_router(interview_routes.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
    seed_quiz_bank()


@app.get("/health")
def health_check():
    return {"status": "ok"}

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

