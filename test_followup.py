# test_followup.py
# followup_generator.py의 quota 없이 테스트 가능한 부분(decide_next_depth, build_followup_prompt)만 확인하는 스크립트.
# 실제 LLM 호출(generate_followup 안의 client.models.generate_content)은 여기서 안 쓴다.

import json
from app.question_generator import pick_code_entity
from app.followup_generator import generate_followup

with open("knowledge_base.json", "r", encoding="utf-8") as f:
    kb = json.load(f)

# 실제 KB에서 코드 하나를 골라서, generate_question()이 만들어줬을 법한 "question" 딕셔너리를 흉내낸다.
entity = pick_code_entity(kb)
fake_question = {
    "question": f"{entity['class_name']}의 {entity['method_name']}는 어떤 기능을 하나요?",
    "level": 1,
    "depth": 0,
    "reference_evidence": {
        "file_path": entity["file_path"],
        "class_name": entity["class_name"],
        "method_name": entity["method_name"],
        "start_line": entity["evidence"]["start_line"],
        "end_line": entity["evidence"]["end_line"],
        "snippet": entity["evidence"]["snippet"],
    },
}
fake_answer = "이 함수는 관련 로직을 처리하는 것 같습니다."
# depth 30 (기준치 80 미만) -> 같은 깊이에 머물러야 정상
fake_evaluation = {"depth": 30, "missing_explanations": "생명주기 관리 방식에 대한 설명이 부족합니다."}

# 여기만 실제 Claude 호출 (유일하게 비용 발생하는 부분)
followup = generate_followup(fake_question, fake_answer, fake_evaluation)
print(json.dumps(followup, ensure_ascii=False, indent=2))