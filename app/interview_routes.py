# 면접 연습(분석 -> 세션 -> 질문 -> 답변 -> 평가) 관련 API 엔드포인트만 모아둔 라우터.

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.analysis_pipeline import analysis_repository
from app.question_generator import generate_question
from app.answer_evaluator import evaluate_answer
from app.followup_generator import generate_followup
from app import store

router = APIRouter()


class AnalyzeRequest(BaseModel):
    repo_url: str


@router.post("/repos/analyze")
def post_repos_analyze(body: AnalyzeRequest):
    repo_id = store.find_repo_by_url(body.repo_url) or store.create_repo(body.repo_url)

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

@router.get("/repos")
def get_repos_list():
    return store.list_repos()

@router.get("/repos/{repo_id}/files")
def get_repos_files(repo_id: str):
    repo = store.get_repo(repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="해당 repo_id를 찾을 수 없습니다.")
    if repo["status"] != "done":
        raise HTTPException(status_code=400, detail="분석이 완료되지 않았습니다.")

    files = [
        {
            "file_path": entry.get("file_path"),
            "priority": entry.get("priority"),
            "reason": entry.get("reason"),
        }
        for entry in repo["knowledge_base"]
    ]
    # priority 숫자가 작을수록(1이 가장 중요) 위로 오게 정렬.
    files.sort(key=lambda f: (f["priority"] is None, f["priority"]))
    return files

@router.delete("/repos/{repo_id}")
def delete_repos(repo_id: str):
    repo = store.get_repo(repo_id)
    if repo is None:
        raise HTTPException(status_code=404, detail="해당 repo_id를 찾을 수 없습니다.")

    store.delete_repo(repo_id)
    return {"repo_id": repo_id, "status": "deleted"}


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

@router.get("/sessions/{session_id}/history")
def get_sessions_history(session_id: str):
    session = store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="해당 session_id를 찾을 수 없습니다.")
    return store.get_session_history(session_id)


@router.get("/sessions/{session_id}/question")
def get_sessions_question(session_id: str):
    session = store.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="해당 session_id를 찾을 수 없습니다.")

    repo = store.get_repo(session["repo_id"])
    question = generate_question(repo["knowledge_base"])
    question_id = store.save_question(session_id, question)

    return {"question_id": question_id, "question": question["question"], "level": question["level"], "reference_evidence": question["reference_evidence"]}


class AnswerRequest(BaseModel):
    answer: str


@router.post("/questions/{question_id}/answer")
def post_questions_answer(question_id: str, body: AnswerRequest):
    question = store.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="해당 question_id를 찾을 수 없습니다.")

    evaluation = evaluate_answer(question, body.answer)
    store.save_evaluation(question_id, evaluation, body.answer)

    return evaluation

@router.get("/questions/{question_id}/followup")
def get_questions_followup(question_id: str):
    question = store.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="해당 question_id를 찾을 수 없습니다.")
    if question["evaluation"] is None:
        raise HTTPException(status_code=400, detail="평가가 없습니다. 답변을 제출하세요.")

    followup = generate_followup(question, question["answer"], question["evaluation"])

    if followup is None:
        return {"question_id": None, "message": "질문이 끝났습니다. 새 질문을 받으세요."}

    followup_id = store.save_question(
        question["session_id"],
        followup,
        parent_question_id=question_id,
        depth=followup["depth"],
    )

    return {"question_id": followup_id, "question": followup["question"], "depth": followup["depth"], "reference_evidence": followup["reference_evidence"]}

@router.get("/weak-topics")
def get_weak_topics_route():
    return store.get_weak_topics()