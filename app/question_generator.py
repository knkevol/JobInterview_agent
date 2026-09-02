# KB에서 근거가 있는 코드를 골라 그 코드를 근거로 삼는 질문 1개를 LLM에게 생성시키는 모듈

import json
import random

# from google import genai
# from google.genai import types

from app.llm_client import generate_json
from dotenv import load_dotenv

load_dotenv()

LEVEL_1_SYSTEM_PROMPT =  """당신은 시니어 개발자 면접관입니다.
지원자가 실제로 작성한 코드(클래스/메서드)를 근거로, "이 프로젝트에서 어떤 기능을
구현했는지"를 확인하는 난이도 1(프로젝트 이해) 수준의 면접 질문을 1개 만드세요.

규칙:
- 반드시 아래에 주어진 코드 근거(evidence)만 참고해서 질문을 만드세요.
- 근거에 없는 내용은 언급하지 마세요. (근거 없는 서술 금지 원칙)
- "이 프로젝트는 어떤 기술을 썼나요?" 같은 단순 지식 확인형 질문은 금지합니다.
- 주어진 클래스/메서드를 구체적으로 지목하며 "어떤 기능을 왜 이렇게 구현했는지"를
  묻는 형태로 작성하세요.
"""

QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string"},
        "level": {"type": "integer"},
    },
    "required": ["question", "level"],
    "additionalProperties": False,
}

def _collect_candidates(knowledge_base: dict) -> list[dict]:
    candidates: list[dict] = []

    for file_entry in knowledge_base:
        for class_info in file_entry.get("classes", []):
            for method_info in class_info.get("methods", []):
                evidence = method_info.get("evidence")
                if evidence is None:
                    continue

                candidates.append({
                    "file_path": file_entry.get("file_path"),
                    "class_name": class_info.get("name"),
                    "method_name": method_info.get("name"),
                    "role": method_info.get("role"),
                    "evidence": evidence
                })
    
    return candidates

def pick_code_entity(knowledge_base: list[dict]) -> dict:
    candidates = _collect_candidates(knowledge_base)

    if not candidates:
        raise ValueError("No candidates found in the knowledge base.")

    return random.choice(candidates)

# 코드 entity를 LLM에게 넘길 텍스트형태로 조합
def build_prompt(entity:dict) -> str:
    evidence = entity["evidence"]
    return f"""파일: {entity['file_path']}
        클래스: {entity['class_name']}
        메서드: {entity['method_name']} (역할: {entity.get('role') or '정보 없음'})

        코드 근거 ({evidence['start_line']}~{evidence['end_line']}줄):
        {evidence['snippet']}
        """

def generate_question(knowledge_base: list[dict]) -> dict:
    entity = pick_code_entity(knowledge_base)
    user_message = build_prompt(entity)

    result = generate_json(
        system_prompt=LEVEL_1_SYSTEM_PROMPT,
        user_message=user_message,
        json_schema=QUESTION_SCHEMA,
        max_tokens=3000,
    )

    result["reference_evidence"] = {
        "file_path": entity["file_path"],
        "class_name": entity["class_name"],
        "method_name": entity["method_name"],
        "start_line": entity["evidence"]["start_line"],
        "end_line": entity["evidence"]["end_line"],
        "snippet": entity["evidence"]["snippet"]
    }

    return result

if __name__ == "__main__":
    with open("knowledge_base.json", "r", encoding="utf-8") as f:
        kb = json.load(f)

    question = generate_question(kb)
    print(json.dumps(question, indent=2, ensure_ascii=False))