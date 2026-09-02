# 질문 + 질문의 근거 코드 + 지원자 답변 => LLM에 전달하여 평가하는 모듈

import json
import re

# from google import genai
# from google.genai import types

from app.llm_client import generate_json
from dotenv import load_dotenv

load_dotenv()

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
"""

EVALUATION_SCHEMA = {
    "type": "object",
    "properties": {
         "score": {"type": "integer"},
        "accuracy": {"type": "integer"},
        "depth": {"type": "integer"},
        "strengths": {"type": "string"},
        "incorrect_points": {"type": "string"},
         "mismatches_with_repo": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {"type": "string"},
                    "evidence_quote": {"type": "string"},
                    "explanation": {"type": "string"},
                },
                "required": ["claim", "evidence_quote", "explanation"],
                "additionalProperties": False,
            },
        },
        "missing_explanations": {"type": "string"},
        "model_answer": {"type": "string"},
        "further_explanation": {"type": "string"},
        "study_recommendations": {"type": "array", "items": {"type": "string"}},
        "related_concepts": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "score", "accuracy", "depth", "strengths", "incorrect_points",
        "mismatches_with_repo", "missing_explanations", "model_answer",
        "further_explanation", "study_recommendations", "related_concepts",
    ],
    "additionalProperties": False,
}

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

def _normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _verify_citations(mismatchs: list[dict], evidence_snippet: str) -> list[dict]:
    normalize_evidence = _normalize_whitespace(evidence_snippet)

    verify_list = []
    for item in mismatchs:
        quote = item.get("evidence_quote", "")
        is_verified = _normalize_whitespace(quote) in normalize_evidence

        verify_list.append({**item, "verified": is_verified})

    return verify_list

def evaluate_answer(question: dict, user_answer: str) -> dict:
    prompt = build_evaluation_prompt(question, user_answer)

    result = generate_json(
        system_prompt=EVALUATION_SYSTEM_PROMPT,
        user_message=prompt,
        json_schema=EVALUATION_SCHEMA,
        max_tokens=6000,
    )
    evidence_snippet = question["reference_evidence"]["snippet"]
    result["mismatches_with_repo"] = _verify_citations(result["mismatches_with_repo"], evidence_snippet)

    return result


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
