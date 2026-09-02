import json
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv
from tree_sitter import Language, Parser
import tree_sitter_cpp as tscpp

from app.github_client import get_file_content
from app.kb_builder import attach_evidence

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"

CPP_LANGUAGE = Language(tscpp.language())

SIGNATURE_ONLY_THRESHOLD = 4000  # 시그니처만 추출할지 여부를 결정하는 임계값

def extract_signature(source_code: str) -> str:
    parser = Parser(CPP_LANGUAGE)
    source_bytes = source_code.encode("utf8")
    tree = parser.parse(source_bytes)
    
    signature_lines: list[str] = []

    def visit(node) -> None:
        if node.type in ["class_specifier", "struct_specifier", "function_definition"]:
            full_text = source_bytes[node.start_byte:node.end_byte].decode("utf8", errors="replace")
            brace_index = full_text.find("{")
            signature = full_text[:brace_index].strip() if brace_index != -1 else full_text
            signature_lines.append(signature.strip())

        for child in node.children:
            visit(child)

    visit(tree.root_node)
    return "\n".join(signature_lines)

CODE_READING_SYSTEM_PROMPT = """당신은 C++/언리얼 엔진 코드를 분석하는 시니어 개발자입니다.
주어진 코드(전체 소스이거나, 클래스/함수 시그니처만 추출된 것일 수 있습니다)를 보고
아래 항목을 추출하세요:
- 클래스/구조체 정의와 상속 관계
- 주요 멤버 변수(이름, 타입, 포인터/참조 여부와 이유로 추정되는 맥락)
- 주요 함수와 그 역할
- 사용된 STL/자료구조
- 메모리 관리 방식(스마트 포인터 사용 여부, 수동 new/delete 여부)
- 디자인 패턴
- 멀티스레딩/네트워크/렌더링/게임플레이 로직 관련 여부

시그니처만 주어졌다면 본문 로직은 추측하지 말고, 이름과 타입에서 합리적으로
유추할 수 있는 선까지만 작성하세요. (근거 없는 서술 금지 원칙)

아래 JSON 형식으로만 답변하세요.
{
  "classes": [
    {
      "name": "클래스명",
      "inherits_from": ["부모클래스"],
      "member_variables": [{"name": "...", "type": "...", "note": "..."}],
      "methods": [{"name": "...", "role": "..."}],
      "design_patterns": ["..."],
      "memory_management": "..."
    }
  ],
  "tech_findings": ["이 파일에서 발견한 기술적 특징들"]
}
"""

def read_code_file(owner: str, repo: str, path: str, branch: str) -> dict:
    source_code = get_file_content(owner, repo, path, branch)

    # 파일 크기에 따라 전체코드 vs 시그니처 추출
    if len(source_code) > SIGNATURE_ONLY_THRESHOLD:
        code_for_llm = extract_signature(source_code)
        content_note = "tree-sitter로 추출한 클래스/함수 시그니처 목록"
    else:
        code_for_llm = source_code
        content_note = "전체 소스 코드"

    user_message = f"""파일 경로: {path}

{content_note}

{code_for_llm}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_message,
        config=types.GenerateContentConfig(
            system_instruction=CODE_READING_SYSTEM_PROMPT,
            temperature=0, 
            max_output_tokens=8000,
            response_mime_type="application/json", 
        ),
    )

    result = json.loads(response.text)

    # LLM이 답하지 않아도 우리가 이미 알고 있는 정보(경로, 언어)는 파이썬 쪽에서 직접 채워 넣는다.
    result["file_path"] = path
    result["language"] = "C++"

    # KB 빌더 : 정확한 코드 발췌
    result = attach_evidence(result, source_code)

    return result

if __name__ == "__main__":
    with open("result.json", "r", encoding="utf-8") as f:
        scanned = json.load(f)
    with open("priority_files.json", "r", encoding="utf-8") as f:
        priority_files = json.load(f)

    # scan_repository()가 조합해둔 걸 다시 분리
    onwer, repo = scanned["repo"].split("/")
    branch = scanned["default_branch"]

    # 성공한 파일 건너뛰기
    if os.path.exists("knowledge_base.json"):
        with open("knowledge_base.json", "r", encoding="utf-8") as f:
            knowledge_base = json.load(f)
    else:
        knowledge_base = []

    # 처리 완료 경로들의 집합
    already_done = {entry["file_path"] for entry in knowledge_base}
    
    for file_info in priority_files[:5]:  # 상위 5개 파일만 분석
        path = file_info["path"]

        if path in already_done:
            print(f"Skip already_done : {path}")
            continue
        
        print(f"Reading {path}...")
        try:
            entry = read_code_file(onwer, repo, path, branch)
            knowledge_base.append(entry)
        except Exception as e:
            print(f"Error reading {path}: {e}")

    with open("knowledge_base.json", "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

    print(f"{len(knowledge_base)}개 파일 처리 완료 -> knowledge_base.json")