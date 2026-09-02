# Github URL을 받아 4단계(구조스캔->우선순위설정->딘계적코드정독->KB빌더)를 순서대로 실행해 최종 KB 리스트를 생성하는 파이프라인 모듈

from app.github_client import scan_repository
from app.file_prioritizer import select_priority_files
from app.code_reader import read_code_file

def analysis_repository(repo_url: str, max_file: int = 5) -> list[dict]:
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

    return knowledge_base