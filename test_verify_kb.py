# 목적: Gemini API를 새로 호출하지 않고, attach_evidence()가 제대로 동작하는지 로컬에서만 검증한다.
# knowledge_base_old.json에 이미 저장돼있는 LLM 결과(classes/methods)를 재사용하고,
# GitHub에서 소스 코드만 다시 받아와서(이건 quota 소모 없음) evidence만 새로 계산해본다.

import json
from app.github_client import get_file_content
from app.kb_builder import attach_evidence

# scan_repository()가 저장해둔 결과에서 owner/repo/branch 정보를 꺼낸다
scanned = json.load(open("result.json", encoding="utf-8"))
owner, repo = scanned["repo"].split("/")
branch = scanned["default_branch"]

# 예전(evidence 개념 도입 전) LLM 호출 결과를 재사용 대상으로 불러온다
old_kb = json.load(open("knowledge_base_old.json", encoding="utf-8"))

for entry in old_kb:
    path = entry["file_path"]

    # GitHub API 호출(소스 코드 텍스트만 받아옴) -> Gemini API와는 완전히 별개라 quota 영향 없음
    source_code = get_file_content(owner, repo, path, branch)

    # 우리가 방금 고친 attach_evidence()를 여기서 직접 실행해본다
    result = attach_evidence(entry, source_code)

    print(f"\n== {path} ==")
    for class_info in result.get("classes", []):
        evidence = class_info.get("evidence")
        # evidence가 있으면 "OK (줄 시작-끝)"로, 없으면 "None"으로 표시
        status = f"OK ({evidence['start_line']}~{evidence['end_line']}줄)" if evidence else "None"
        print(f"  class {class_info.get('name')}: {status}")

        for method_info in class_info.get("methods", []):
            m_evidence = method_info.get("evidence")
            if m_evidence:
                # 코드 발췌의 첫 줄만 미리보기로 보여준다 (전체를 다 찍으면 너무 길어지니까)
                first_line = m_evidence["snippet"].splitlines()[0]
                print(f"    method {method_info.get('name')}: OK ({m_evidence['start_line']}~{m_evidence['end_line']}줄) -> {first_line}")
            else:
                print(f"    method {method_info.get('name')}: None")