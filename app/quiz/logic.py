# CS 퀴즈 로직

import random
from datetime import datetime, timezone

from app.db import get_connection, init_db
from app.quiz.seed_data import QUIZ_SEED_DATA

def seed_quiz_bank() -> None:
    # DB 초기화
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) FROM quiz_bank").fetchone()[0]
        if count > 0:
            print(f"quiz_bank에 이미 {count}개 문제가 있어서 건너뜁니다.")
            return
        for quiz in QUIZ_SEED_DATA:
            conn.execute(
                "INSERT INTO quiz_bank (category, question, answer, explanation, difficulty) VALUES (?, ?, ?, ?, ?)",
                (quiz["category"], quiz["question"], quiz["answer"], quiz["explanation"], quiz["difficulty"])
            )
        conn.commit()
        print(f"{len(QUIZ_SEED_DATA)}개 문제를 quiz_bank에 채워 넣었습니다.")
    finally:
        conn.close()

def get_random_quiz(session_id: str) -> dict | None:
    # 안풀어본 문제 반환
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT id, category, question, difficulty
            FROM quiz_bank
            WHERE id NOT IN (
                SELECT quiz_id FROM quiz_history WHERE session_id = ?
            )
            """, (session_id,)).fetchall()
    finally:
        conn.close()

    if not rows:
        return None

    chosen_row = random.choice(rows)
    return dict(chosen_row)

def submit_quiz_answer(quiz_id: int, session_id: str, submitted_answer: str) -> dict:
    conn = get_connection()
    try:
        quiz_row = conn.execute(
            "SELECT answer, explanation FROM quiz_bank WHERE id = ?",
            (quiz_id,),
        ).fetchone()

        if quiz_row is None:
            raise ValueError(f"quiz_id {quiz_id}에 해당하는 퀴즈가 없습니다.")

        # strip(): 앞뒤 공백 제거, lower(): 대소문자 통일
        is_correct = submitted_answer.strip().lower() == quiz_row["answer"].strip().lower()

        conn.execute(
            """
            INSERT INTO quiz_history (quiz_id, session_id, is_correct, answered_at)
            VALUES (?, ?, ?, ?)
            """,
            (quiz_id, session_id, int(is_correct), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()

        return {
            "is_correct": is_correct,
            "correct_answer": quiz_row["answer"],
            "explanation": quiz_row["explanation"],
        }
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    seed_quiz_bank()

    fake_session_id = "dev-test-session"

    quiz = get_random_quiz(fake_session_id)
    print("\n=== 오늘의 퀴즈 ===")
    print(f"[{quiz['category']}] {quiz['question']}")

    result = submit_quiz_answer(quiz["id"], fake_session_id, "이건 오답입니다")
    print("\n=== 채점 결과 ===")
    print(f"정답 여부: {result['is_correct']}")
    print(f"정답: {result['correct_answer']}")
    print(f"해설: {result['explanation']}")

    next_quiz = get_random_quiz(fake_session_id)
    print("\n=== 같은 세션으로 다시 조회 (방금 푼 문제 제외되는지 확인) ===")
    if next_quiz:
        print(f"[{next_quiz['category']}] {next_quiz['question']} (id={next_quiz['id']}, 방금 문제 id={quiz['id']}와 달라야 정상)")
    else:
        print("풀 수 있는 문제가 더 없습니다.")