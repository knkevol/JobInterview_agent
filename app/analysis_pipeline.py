# Github URL을 받아 4단계(구조스캔->우선순위설정->딘계적코드정독->KB빌더)를 순서대로 실행해 최종 KB 리스트를 생성하는 파이프라인 모듈

import json
import hashlib
from pathlib import Path

from app.github_client import scan_repository
from app.file_prioritizer import select_priority_files
from app.code_reader import read_code_file

CACHE_DIR = Path(__file__).resolve().parent.parent / "analysis_cache"

# 동일한 URL에 대하여 중복처리 방지
def _cache_path(repo_url: str) -> Path:
    CACHE_DIR.mkdir(exist_ok=True)
    url_hash = hashlib.sha256(repo_url.encode()).hexdigest()[:16]
    return CACHE_DIR / f"{url_hash}.json"

def analysis_repository(repo_url: str, max_file: int = 5) -> list[dict]:
    cache_path = _cache_path(repo_url)

    if cache_path.exists():
        print(f"캐시된 분석 결과 재사용 : {cache_path}")
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
        
    # 1단계: 저장소 구조 스캔
    scanned = scan_repository(repo_url)
    owner, repo = scanned["repo"].split("/")
    branch = scanned["default_branch"]
    
    # 2단계: 우선순위 파일 선정
    priority_files = select_priority_files(readme=scanned["readme"], file_tree=scanned["file_tree"])
    
    # 3. 4단계: 단계적 코드 정독 + KB 빌더
    knowledge_base: list[dict] = []
    for file_info in priority_files[:max_file]:
        path = file_info["path"]
        try:
            entry = read_code_file(owner, repo, path, branch)
            knowledge_base.append(entry)
        except Exception as e:
            print(f"Error reading {path}: {e}")

    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

    return knowledge_base