# 코드 분석 결과/세션/질문 상태를 메모리에 보관 
# 서버가 켜져있는 동안만 유지.

import json
import uuid
from collections import Counter
from datetime import datetime, timezone

from app.db import get_connection

_repos: dict[str, dict] = {}
_sessions: dict[str, dict] = {}
_questions: dict[str, dict] = {}

def _new_id() -> str:
    return str(uuid.uuid4()) # 무작위 고유 문자열을 만드는 표준 라이브러리 함수.

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def create_repo(repo_url: str) -> str:
    repo_id = _new_id()
    conn = get_connection()

    try:
        conn.execute("INSERT INTO repositories (id, repo_url, status, knowledge_base_json, error, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (repo_id, repo_url, "pending", None, None, _now()),
        )
        conn.commit()
    finally:
        conn.close()

    return repo_id

def get_repo(repo_id: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM repositories WHERE id = ?", (repo_id,)).fetchone()
    finally:
        conn.close()

        if row is None:
            return None
        
    return {
        "repo_id": row["id"],
        "repo_url": row["repo_url"],
        "status": row["status"],
        "knowledge_base": json.loads(row["knowledge_base_json"]) if row["knowledge_base_json"] else None,
        "error": row["error"],
        }

def mark_repo_done(repo_id: str, knowledge_base: list[dict])-> None:
    conn = get_connection()
    try:
        # ensure_ascii=False > 한글
        conn.execute(
            "UPDATE repositories SET status = ?, knowledge_base_json = ? WHERE id = ?",
            ("done", json.dumps(knowledge_base, ensure_ascii=False), repo_id),
        )
        conn.commit()
    finally:
        conn.close()

def mark_repo_error(repo_id: str, error_message: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE repositories SET status = ?, error = ? WHERE id = ?",
            ("error", error_message, repo_id),
        )
        conn.commit()
    finally:
        conn.close()

def create_session(repo_id: str) -> str:
    session_id = _new_id()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO sessions (id, repo_id, created_at) VALUES (?, ?, ?)",
            (session_id, repo_id, _now()),
        )
        conn.commit()
    finally:
        conn.close()
    return session_id

def get_session(session_id: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    return {"session_id": row["id"], "repo_id": row["repo_id"]}

def save_question(session_id: str, question: dict, parent_question_id: str | None = None, depth: int = 0) -> str:
    question_id = _new_id()
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO questions (id, session_id, parent_question_id, depth, question_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (question_id, session_id, parent_question_id, depth, json.dumps(question, ensure_ascii=False), _now()),
        )
        conn.commit()
    finally:
        conn.close()
    return question_id

def get_question(question_id: str) -> dict | None:
    conn = get_connection()
    try:
        q_row = conn.execute("SELECT * FROM questions WHERE id = ?", (question_id,)).fetchone()
        if q_row is None:
            return None

        # id 역순(DESC)으로 정렬해서 가장 최근 평가 1건만 LIMIT 1로 가져온다.
        eval_row = conn.execute(
            "SELECT * FROM evaluations WHERE question_id = ? ORDER BY id DESC LIMIT 1",
            (question_id,),
        ).fetchone()
    finally:
        conn.close()

    result = {
        **json.loads(q_row["question_json"]),
        "question_id": q_row["id"],
        "session_id": q_row["session_id"],
        "parent_question_id": q_row["parent_question_id"],
        "depth": q_row["depth"],
        "evaluation": json.loads(eval_row["evaluation_json"]) if eval_row else None,
    }

    # 답변 없을 시 answer키 자체를 생성하지 않음
    if eval_row:
        result["answer"] = eval_row["answer_text"]

    return result

def save_evaluation(question_id: str, evaluation: dict, answer: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO evaluations (question_id, answer_text, evaluation_json, created_at) VALUES (?, ?, ?, ?)",
            (question_id, answer, json.dumps(evaluation, ensure_ascii=False), _now()),
        )
        conn.commit()
    finally:
        conn.close()

def get_session_history(session_id: str) -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT
                q.id AS question_id,
                q.parent_question_id,
                q.depth,
                q.question_json,
                q.created_at AS question_created_at,
                e.answer_text,
                e.evaluation_json
            FROM questions q
            LEFT JOIN evaluations e ON e.question_id = q.id
            WHERE q.session_id = ?
            ORDER BY q.created_at ASC
        """, (session_id,)).fetchall()
    finally:
        conn.close()

    history = []
    for row in rows:
        # db에서 가져온 row를 파이썬 딕셔너리로 변환
        entry = {
            **json.loads(row["question_json"]),
            "question_id": row["question_id"],
            "parent_question_id": row["parent_question_id"],
            "depth": row["depth"],
            "evaluation": json.loads(row["evaluation_json"]) if row["evaluation_json"] else None,
        }
        if row["answer_text"] is not None:
            entry["answer"] = row["answer_text"]
        history.append(entry)

    return history

def get_weak_topics() -> list[dict]:
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT
                q.id AS question_id,
                q.question_json,
                e.evaluation_json
            FROM evaluations e
            JOIN questions q ON q.id = e.question_id
        """).fetchall()
    finally:
        conn.close()

    topic_counts = Counter()
    topic_occurrences: dict[str, list[dict]] = {}

    for row in rows:
        evaluation = json.loads(row["evaluation_json"])
        question = json.loads(row["question_json"])

        for concept in evaluation.get("related_concepts", []):
            topic_counts[concept] += 1
            topic_occurrences.setdefault(concept, []).append({
                "question_id": row["question_id"],
                "question": question.get("question"),
                "score": evaluation.get("score"),
                "missing_explanations": evaluation.get("missing_explanations"),
            })

    result = []
    for topic, count in topic_counts.most_common():
        if count < 2:
            continue
        result.append({
            "topic": topic,
            "occurrence_count": count,
            "occurrences": topic_occurrences[topic],
        })

    return result