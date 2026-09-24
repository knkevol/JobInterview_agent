import json
from app.analysis_pipeline import analysis_repository

kb = analysis_repository("https://github.com/knkevol/Robo_CopyProject")

print(f"{len(kb)}개 파일 분석 완료")
for entry in kb:
    class_names = [c["name"] for c in entry.get("classes", [])]
    print(f"  {entry['file_path']}: {class_names}")

with open("knowledge_base_claude.json", "w", encoding="utf-8") as f:
    json.dump(kb, f, ensure_ascii=False, indent=2)
print("-> knowledge_base_claude.json 저장 완료")
