# 목적: EVALUATION_SYSTEM_PROMPT가 실제로 몇 토큰인지 확인
# (Haiku 4.5 캐싱 최소 기준인 4096 토큰을 넘는지 보려는 것)
from anthropic import Anthropic
from app.answer_evaluator import EVALUATION_SYSTEM_PROMPT  # 확인하고 싶은 프롬프트로 바꿔도 됨

client = Anthropic()
resp = client.messages.count_tokens(
    model="claude-haiku-4-5",  # 실제 쓰는 모델과 동일해야 정확함 (모델별로 토크나이저 다름)
    messages=[{"role": "user", "content": "x"}],  # user 메시지는 필수라 더미로 채움
    system=EVALUATION_SYSTEM_PROMPT,
)
print(resp.input_tokens)