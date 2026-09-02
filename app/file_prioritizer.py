import json
import os

from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL_NAME = "gemini-3.6-flash"


PRIORITIZATION_SYSTEM_PROMPT = """당신은 코드 리뷰 경험이 많은 시니어 개발자입니다.
주어진 저장소의 README와 파일 목록만 보고, 개발자 면접 질문을 만들기 위해
자세히 읽어야 할 파일을 선정하는 것이 당신의 역할입니다.

우선순위를 정할 때 다음을 우선하세요:
- 엔트리 포인트(main, index 등)
- 핵심 클래스/모듈이 정의된 파일
- 디렉토리 구조상 중심적인 역할을 하는 파일

아래 JSON 배열 형식으로 답변하세요.
[
  {"path": "파일 경로", "priority": 1, "reason": "선정 이유"}
]
"""

def build_file_list_text(file_tree: list[dict]) -> str:
    file_lines = [
        f"{item['path']} ({item.get('size', 0)} bytes)"
        for item in file_tree
        if item["type"] == "blob"
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

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_message,
        config=types.GenerateContentConfig(
         system_instruction=PRIORITIZATION_SYSTEM_PROMPT,
            temperature=0,
            max_output_tokens=8000,
            response_mime_type="application/json",
        ),
    )

    return json.loads(response.text)


if __name__ == "__main__":
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