import random

from app.llm_client import generate_json

LLM_QUIZ_CATEGORIES = ["자료구조", "알고리즘", "운영체제", "네트워크", "데이터베이스", "C++", "메모리관리", "멀티스레딩/동시성", "프로파일링/최적화"]

LLM_QUIZ_GENERATE_SYSTEM_PROMPT = """당신은 게임 클라이언트/서버 개발자를 채용하는 면접관입니다.
지원자는 게임 프로그래머로, 아래와 같은 업무를 주로 담당합니다.
- 클라이언트·서버·엔진 개발
- C++, C# 등을 활용해 게임 콘텐츠와 시스템 구현
- 디버깅·리팩토링·최적화 작업 수행
- 툴 제작 및 자동화 업무
- 기능 구현과 라이브 서비스 대응

주어진 카테고리 하나에서, 위 업무를 실제로 수행하는 데 필요한 CS 개념을
확인하는 짧은 질문 1개를 만드세요.

규칙:
- 순수 암기식 정의를 묻지 말고, 게임 개발 상황에서 실제로카테 마주치는 맥락으로
  질문하세요. (예: "멀티플레이어 동기화에서 이 자료구조를 쓰는 이유",
  "프레임 드랍이 발생했을 때 의심해볼 원인", "런타임에 매 프레임 동적 할당을
  피해야 하는 이유" 등)
- 코드를 짜라고 하거나 긴 서술을 요구하지 말고, 개념 하나를 짧게 설명하게 만드는
  질문으로 작성하세요.
- 같은 카테고리라도 매번 다른 세부 개념을 물어보도록 다양하게 만드세요.
"""

LLM_QUIZ_GENERATE_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
    },
    "required": ["question"],
    "additionalProperties": False,
}

LLM_QUIZ_EVALUATE_SYSTEM_PROMPT = """당신은 CS 기초 지식을 채점하는 면접관입니다.
주어진 질문과 지원자의 답변을 보고, 답변이 개념적으로 맞는지 판단하세요.

채점 기준:
- 용어를 토씨 하나 안 틀리고 맞혀야 정답인 게 아니라, 핵심 개념을 정확히
  이해하고 설명했으면 정답으로 인정하세요.
- 부분적으로만 맞았거나 핵심을 놓쳤다면 오답으로 판단하고, explanation에
  뭐가 부족한지 설명하세요.
"""

LLM_QUIZ_EVALUATE_SCHEMA = {
    "type": "object",
    "properties": {
        "is_correct": {"type": "boolean"},
        "model_answer": {"type": "string"},
        "explanation": {"type": "string"},
    },
    "required": ["is_correct", "model_answer", "explanation"],
    "additionalProperties": False,
}

def generate_llm_quiz(category: str | None = None) -> dict:
    chosen_category = category or random.choice(LLM_QUIZ_CATEGORIES)

    user_message = f"카테고리 : {chosen_category}"

    result = generate_json(
        system_prompt=LLM_QUIZ_GENERATE_SYSTEM_PROMPT,
        user_message=user_message,
        json_schema=LLM_QUIZ_GENERATE_SCHEMA,
        max_tokens=1500,
    )

    result["category"] = chosen_category
    return result

def evaluate_llm_quiz_answer(question: str, category: str, user_answer: str) -> dict:
    user_message = f"""[카테고리]
{category}

[질문]
{question}

[지원자의 답변]
{user_answer}
"""

    return generate_json(
        system_prompt=LLM_QUIZ_EVALUATE_SYSTEM_PROMPT,
        user_message=user_message,
        json_schema=LLM_QUIZ_EVALUATE_SCHEMA,
        max_tokens=1500,
    )

if __name__ == "__main__":
    quiz = generate_llm_quiz()
    print("=== 생성된 문제 ===")
    print(f"[{quiz['category']}] {quiz['question']}")

    fake_answer = "그냥 아무거나 저장하는 자료구조입니다."
    result = evaluate_llm_quiz_answer(quiz["question"], quiz["category"], fake_answer)

    print("\n=== 채점 결과 ===")
    print(f"정답 여부: {result['is_correct']}")
    print(f"모범 답안: {result['model_answer']}")
    print(f"설명: {result['explanation']}")