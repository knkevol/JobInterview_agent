from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.quiz.logic import get_random_quiz, submit_quiz_answer
from app.quiz.llm_quiz import generate_llm_quiz, evaluate_llm_quiz_answer

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

class LLMQuizAnswerRequest(BaseModel):
    question: str
    category: str
    answer: str

@router.get("/quiz/llm/generate")
def get_quiz_llm_generate(category: str | None = None):
    return generate_llm_quiz(category)

@router.post("/quiz/llm/answer")
def post_quiz_llm_answer(body: LLMQuizAnswerRequest):
    return evaluate_llm_quiz_answer(body.question, body.category, body.answer)

@router.post("/quiz/{quiz_id}/answer")
def post_quiz_answer(quiz_id: int, body: QuizAnswerRequest):
    try:
        return submit_quiz_answer(quiz_id, body.session_id, body.answer)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

