from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.quiz.logic import get_random_quiz, submit_quiz_answer

router = APIRouter()

class QuizAnswerRequest(BaseModel):
    session_id: str
    answer: str


@router.get("/quiz/random")
def get_quiz_random(session_id: str):
    quiz = get_random_quiz(session_id)
    if quiz is None:
        raise HTTPException(status_code=404, detail="풀 수 있는 퀴즈가 더 이상 없습니다.")
    return quiz


@router.post("/quiz/{quiz_id}/answer")
def post_quiz_answer(quiz_id: int, body: QuizAnswerRequest):
    try:
        return submit_quiz_answer(quiz_id, body.session_id, body.answer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))