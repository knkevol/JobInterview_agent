# 면접 연습(분석 -> 세션 -> 질문 -> 답변 -> 평가) 관련 API 엔드포인트만 모아둔 라우터.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.analysis_pipeline import analysis_repository
from app.question_generator import generate_question
from app.answer_evaluator import evaluate_answer
from app import store

router = APIRouter()


class AnalyzeRequest(BaseModel):
    repo_url: str


@router.post("/repos/analyze")
def post_repos_analyze(body: AnalyzeRequest):
    repo_id = store.create_repo(body.repo_url)

    try:
        knowledge_base = analysis_repository(body.repo_url)
        store.mark_repo_done(repo_id, knowledge_base)
    except Exception as e:
        store.mark_repo_error(repo_id, str(e))
        raise HTTPException(status_code=500, detail=f"분석 실패: {e}")

    return {"repo_id": repo_id, "status": "done", "file_count": len(knowledge_base)}


@router.get("/repos/{repo_id}/status")
def get_repos_status(repo_id: str):
    repo = store.get_repo(repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="해당 repo_id를 찾을 수 없습니다.")
    return {"repo_id": repo_id, "status": repo["status"], "error": repo["error"]}


class CreateSessionRequest(BaseModel):
    repo_id: str


@router.post("/sessions")
def post_sessions(body: CreateSessionRequest):
    repo = store.get_repo(body.repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="해당 repo_id를 찾을 수 없습니다.")
    if repo["status"] != "done":
        raise HTTPException(status_code=400, detail="분석 진행중입니다.")

    session_id = store.create_session(body.repo_id)
    return {"session_id": session_id}


@router.get("/sessions/{session_id}/question")
def get_sessions_question(session_id: str):
    session = store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="해당 session_id를 찾을 수 없습니다.")

    repo = store.get_repo(session["repo_id"])
    question = generate_question(repo["knowledge_base"])
    question_id = store.save_question(session_id, question)

    return {"question_id": question_id, "question": question["question"], "level": question["level"]}


class AnswerRequest(BaseModel):
    answer: str


@router.post("/questions/{question_id}/answer")
def post_questions_answer(question_id: str, body: AnswerRequest):
    question = store.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="해당 question_id를 찾을 수 없습니다.")

    evaluation = evaluate_answer(question, body.answer)
    store.save_evaluation(question_id, evaluation)

    return evaluation