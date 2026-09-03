# 이 프로젝트의 모든 LLM 호출이 거쳐가는 단일 통로.

import json

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic()
# MODEL_NAME = "claude-sonnet-5"
MODEL_NAME = "claude-haiku-4-5"

# 시스템 프롬프트 + 유저 메시지를 Claude로 보내고 json으로 돌려 받음
def generate_json(system_prompt: str, user_message: str, json_schema: dict, max_tokens: int = 4000, temperature: float = 0.5) -> dict:
    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
        output_config={
            "format": {
                "type": "json_schema",
                "schema": json_schema,
            }
        },
    )

    text = next(block.text for block in response.content if block.type == "text")
    return json.loads(text)

if __name__ == "__main__":
    schema = {
        "type": "object",
        "properties": {"greeting": {"type": "string"}},
        "required": ["greeting"],
        "additionalProperties": False,
    }
    result = generate_json("당신은 친절한 인사봇입니다.", "안녕이라고 인사해줘.", schema, max_tokens=100)
    print(result)