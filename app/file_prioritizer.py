import json
import os

# from google import genai
# from google.genai import types
from app.llm_client import generate_json
from dotenv import load_dotenv

load_dotenv()

PRIORITIZATION_SYSTEM_PROMPT = """당신은 코드 리뷰 경험이 많은 시니어 개발자입니다.
주어진 저장소의 README와 파일 목록만 보고, 개발자 면접 질문을 만들기 위해
자세히 읽어야 할 파일을 선정하는 것이 당신의 역할입니다.

우선순위를 정할 때 다음을 우선하세요:
- 엔트리 포인트(main, index 등)
- 핵심 클래스/모듈이 정의된 파일
- 디렉토리 구조상 중심적인 역할을 하는 파일

files 배열 안에 {"path": "파일 경로", "priority": 1, "reason": "선정 이유"} 형태로 답변하세요.
"""

PRIORITIZATION_SCHEMA = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "priority": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["path", "priority", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["files"],
    "additionalProperties": False,
}

# 분석 대상 파일 확장자 화이트리스트
CODE_FILE_SUFFIXES = (".cpp", ".h", ".hpp", ".Build.cs", ".Target.cs", ".uproject")

def _is_code_file(path: str) -> bool:
    return path.endswith(CODE_FILE_SUFFIXES)

def build_file_list_text(file_tree: list[dict]) -> str:
    file_lines = [
        f"{item['path']} ({item.get('size', 0)} bytes)"
        for item in file_tree
        if item["type"] == "blob" and _is_code_file(item["path"])
    ]
    
    return "\n".join(file_lines)

def select_priority_files(readme: str | None, file_tree: list[dict], max_files: int = 15) -> list[dict]:
    file_list_text = build_file_list_text(file_tree)

    user_message = f"""다음은 GitHub 저장소 정보입니다.

[README]
{readme or "(README 없음)"}

[파일 목록]
{file_list_text}

위 정보를 참고하여, 최대 {max_files}개까지 파일을 우선순위와 함께 선정해주세요.
"""

    result = generate_json(
        PRIORITIZATION_SYSTEM_PROMPT,
        user_message,
        PRIORITIZATION_SCHEMA,
        max_tokens=8000,
    )

    return result["files"]


if __name__ == "__main__":
    import json

    with open("result.json", "r", encoding="utf-8") as f:
        scanned = json.load(f)

    priority_files = select_priority_files(
        readme=scanned["readme"],
        file_tree=scanned["file_tree"],
    )

    with open("priority_files.json", "w", encoding="utf-8") as f:
        json.dump(priority_files, f, indent=2, ensure_ascii=False)

    print("priority_files.json 파일로 저장")
    print(json.dumps(priority_files, indent=2, ensure_ascii=False))