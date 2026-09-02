# 코드 분석 결과/세션/질문 상태를 메모리에 보관 
# 서버가 켜져있는 동안만 유지.

import uuid

_repos: dict[str, dict] = {}
_sessions: dict[str, dict] = {}
_questions: dict[str, dict] = {}

def _new_id() -> str:
    return str(uuid.uuid4())

def create_repo(repo_url: str) -> str:
    repo_id = _new_id()
    _repos[repo_id] = {
         "repo_id": repo_id,
        "repo_url": repo_url,
        "status": "pending",
        "knowledge_base": None,
        "error": None,
    }
    return repo_id

def get_repo(repo_id: str) -> dict | None:
    return _repos.get(repo_id)

def mark_repo_done(repo_id: str, knowledge_base: list[dict])-> None:
    _repos[repo_id]["status"] = "done"
    _repos[repo_id]["knowledge_base"] = knowledge_base

def mark_repo_error(repo_id: str, error_message: str) -> None:
    _repos[repo_id]["status"] = "error"
    _repos[repo_id]["error"] = error_message

def create_session(repo_id: str) -> str:
    session_id = _new_id()
    _sessions[session_id] = {"session_id": session_id, "repo_id": repo_id}
    return session_id

def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)

def save_question(session_id: str, question: dict) -> str:
    question_id = _new_id()
    _questions[question_id] = {
        "question_id": question_id,
        "session_id": session_id,
        **question,  # question 딕셔너리 : (question/level/reference_evidence)
        "evaluation": None,
    }
    return question_id

def get_question(question_id: str) -> dict | None:
    return _questions.get(question_id)

def save_evaluation(question_id: str, evaluation: dict) -> None:
    _questions[question_id]["evaluation"] = evaluation