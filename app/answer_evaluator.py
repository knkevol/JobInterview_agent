# 질문 + 질문의 근거 코드 + 지원자 답변 => LLM에 전달하여 평가하는 모듈

import json
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"

EVALUATION_SYSTEM_PROMPT = """당신은 시니어 개발자 면접관입니다.
아래 세 가지 정보를 참고해서 지원자의 답변을 평가하세요.
1. 면접 질문
2. 그 질문이 근거로 삼은 실제 코드(evidence)
3. 지원자의 답변

평가 기준 (6가지):
1. 실제 프로젝트 구현과 답변의 일치 여부
2. 기술적으로 올바른 설명인지
3. 구현 방법을 정확히 이해하고 있는지
4. 구현 방법을 선택한 이유를 설명할 수 있는지
5. 관련 언어/기술 원리에 대한 이해도
6. 다른 구현 방법과 비교한 장단점 설명 능력

중요한 원칙:
- "정석적으로는 맞지만 이 프로젝트의 실제 구현과는 다르다"와 "기술적으로 틀렸다"는
  서로 다른 문제이니 반드시 구분해서 설명하세요. (mismatches_with_repo / incorrect_points를
  절대 섞지 마세요.)
- 실제 구현과 다른 내용을 답했다면, 어떤 부분이 왜 다른지 evidence를 인용해서
  구체적으로 설명하세요.
- 주어진 evidence에 없는 내용을 "실제로 이렇게 구현되어 있다"는 식으로 지어내지 마세요.
  (근거 없는 서술 금지 원칙)

아래 JSON 형식으로만 답변하세요.
{
  "score": 0~100 사이 정수 (총점),
  "accuracy": 0~100 사이 정수 (실제 구현과의 일치도),
  "depth": 0~100 사이 정수 (설명의 깊이/충실도),
  "strengths": "답변의 장점",
  "incorrect_points": "기술적으로 잘못된 내용 (없으면 빈 문자열)",
  "mismatches_with_repo": "실제 프로젝트 구현과 다른 내용, evidence 인용 포함 (없으면 빈 문자열)",
  "missing_explanations": "부족한 설명 (없으면 빈 문자열)",
  "model_answer": "정석적인 모범 답변",
  "further_explanation": "해당 질문에 대한 추가 설명",
  "study_recommendations": ["추가로 공부할 개발 지식 목록"],
  "related_concepts": ["관련된 언어/기술 개념 태그"]
}
"""

def build_evaluation_prompt(question: dict, user_answer: str) -> str:
    # LLM에게 전달할 텍스트로 조립
    evidence = question["reference_evidence"]

    return f"""[면접 질문]
{question['question']}

[질문이 근거로 삼은 실제 코드]
파일: {evidence['file_path']}
클래스: {evidence['class_name']}
메서드: {evidence['method_name']}
코드 ({evidence['start_line']}~{evidence['end_line']}줄):
{evidence['snippet']}

[지원자의 답변]
{user_answer}
"""

def evaluate_answer(question: dict, user_answer: str) -> dict:
    prompt = build_evaluation_prompt(question, user_answer)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=EVALUATION_SYSTEM_PROMPT,
            temperature=0.3,
            max_output_tokens=2000,
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)

if __name__ == "__main__":
    import json as _json
    from app.question_generator import generate_question

    with open("knowledge_base.json", "r", encoding="utf-8") as f:
        kb = _json.load(f)

    question = generate_question(kb)
    print("=== 생성된 질문 ===")
    print(question["question"])

    fake_answer = "이 함수는 데미지를 처리하는 함수인 것 같습니다."
    evaluation = evaluate_answer(question, fake_answer)

    print("\n=== 평가 결과 ===")
    print(json.dumps(evaluation, ensure_ascii=False, indent=2))