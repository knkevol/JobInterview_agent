import json

# from google import genai
# from google.genai import types
from app.llm_client import generate_json
from dotenv import load_dotenv

load_dotenv()

# index = depth
DEPTH_TOPICS = [
    "프로젝트 기능",
    "구현 방법",
    "코드 구조",
    "자료형 선택 이유",
    "메모리 / 성능",
    "언어 원리",
    "대안 설계",
    "예외 상황 / 개선",
]
MAX_DEPTH = len(DEPTH_TOPICS) - 1  # 7

DEPTH_ADVANCE_THRESHOLD = 80

FOLLOWUP_SYSTEM_PROMPT = """당신은 시니어 개발자 면접관입니다.
지원자가 방금 한 답변을 보고, 같은 코드에 대해 더 깊이 파고드는 꼬리질문을 1개 만드세요.

꼬리질문은 아래 8단계 깊이 중 하나에 속합니다.
0. 프로젝트 기능 - "어떤 기능을 구현했나요?"
1. 구현 방법 - "어떤 방식으로 구현했나요?"
2. 코드 구조 - "이 클래스/함수는 어떤 역할을 하나요?"
3. 자료형 선택 이유 - "왜 이 자료형/자료구조를 썼나요?"
4. 메모리 / 성능 - "이 객체의 생명주기는 어떻게 관리되나요?"
5. 언어 원리 - "참조로 바꾸면 어떤 차이가 생기나요?"
6. 대안 설계 - "다른 설계 방법이 있다면 무엇인가요?"
7. 예외 상황 / 개선 - "객체 수가 늘어나면 어떤 문제가 생길까요?"

이번에 만들 질문의 목표 깊이는 [목표 깊이]에 명시되어 있습니다.
- 목표 깊이가 이전 질문과 같다면: 지원자가 이전 깊이의 핵심 개념을 얕게만 언급했다는 뜻이니,
  같은 주제를 더 구체적으로 파고드는 질문을 만드세요.
- 목표 깊이가 이전 질문보다 깊어졌다면: 지원자가 충분히 설명했다는 뜻이니,
  다음 단계 주제로 넘어가는 질문을 만드세요.

반드시 주어진 코드 근거(evidence)만 참고하고, 근거에 없는 내용은 지어내지 마세요.
"""

FOLLOWUP_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
    },
    "required": ["question"],
    "additionalProperties": False,
}

def decide_next_depth(current_depth: int, evaluation: dict) -> int:
    if evaluation["depth"] >= DEPTH_ADVANCE_THRESHOLD:
        return min(current_depth + 1, MAX_DEPTH)
    return current_depth

def build_followup_prompt(question: dict, user_answer: str, evaluation: dict, current_depth:int, next_depth: int) -> str:
    evidence = question["reference_evidence"]

    return f"""[코드 근거]
파일: {evidence['file_path']}
클래스: {evidence['class_name']}
메서드: {evidence['method_name']}
코드 ({evidence['start_line']}~{evidence['end_line']}줄):
{evidence['snippet']}

[이전 질문] (깊이 {current_depth}: {DEPTH_TOPICS[current_depth]})
{question['question']}

[지원자의 답변]
{user_answer}

[평가에서 지적된 부족한 설명]
{evaluation.get('missing_explanations') or '(없음)'}

[목표 깊이]
{next_depth}: {DEPTH_TOPICS[next_depth]}
"""

def generate_followup(question: dict, user_anser: str, evaluation: dict) -> dict | None:
    current_depth = question.get("depth", 0)

    if current_depth == MAX_DEPTH and evaluation["depth"] >= DEPTH_ADVANCE_THRESHOLD:
        return None

    next_depth = decide_next_depth(current_depth, evaluation)
    prompt = build_followup_prompt(question, user_anser, evaluation, current_depth, next_depth)

    result = generate_json(
        system_prompt=FOLLOWUP_SYSTEM_PROMPT,
        user_message=prompt,
        json_schema=FOLLOWUP_SCHEMA,
        max_tokens=3000,
    )
    result["depth"] = next_depth
    result["reference_evidence"] = question["reference_evidence"]

    return result