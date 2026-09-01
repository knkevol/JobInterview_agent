import base64
import os
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일을 읽어 키값을 os.environ에 등록
load_dotenv()

GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        return headers

def parse_repo_url(url: str) -> tuple[str, str]:
    parsed = urlparse(url.strip())

    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Invalid GitHub repository URL: {url}")

    owner, repo = parts[0], parts[1]

    if repo.endswith(".git"):
        repo = repo[:-4]

    return owner, repo

def get_repo_info(owner: str, repo: str) -> dict:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}"
    response = requests.get(url, headers=_headers())
    response.raise_for_status()
    return response.json()

# 언어별 바이트 수 통계
def get_languages(owner: str, repo: str) -> dict:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/languages"
    response = requests.get(url, headers=_headers())
    response.raise_for_status()
    return response.json()

def get_readme(owner: str, repo: str) -> str | None:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/readme"
    response = requests.get(url, headers=_headers())

    if response.status_code == 404:
        return None
    
    response.raise_for_status()
    readme_data = response.json()

    # 깃허브 API로 인코딩된 base64를 디코딩하여 문자열로 변환
    decoded_bytes = base64.b64decode(readme_data["content"])
    return decoded_bytes.decode("utf-8", errors="replace")


def get_file_tree(owner: str, repo: str, branch: str = "") -> list[dict]:
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/git/trees/{branch}"
    # recursive 1 을 설정해야 하위 폴더까지 재귀적으로 펼쳐짐
    response = requests.get(url, headers=_headers(), params={"recursive": "1"})
    response.raise_for_status()
    data = response.json()

    if data.get("truncated"):
        print("The file tree is too large to retrieve. Please use a smaller repository or a specific branch.")

    # 리스트 컴프리헨션 : tree의 item에서 path, type, size를 추출하여 새로운 리스트를 반환
    return [
        {"path": item["path"], "type": item["type"], "size": item.get("size")}
        for item in data["tree"]
    ]

# 조합
def scan_repository(repo_url: str) -> dict:
    owner, repo = parse_repo_url(repo_url)
    info = get_repo_info(owner, repo)
    branch = info["default_branch"]

    return {
       "repo": f"{owner}/{repo}",
        "default_branch": branch,
        "description": info.get("description"),
        "languages": get_languages(owner, repo),
        "readme": get_readme(owner, repo),
        "file_tree": get_file_tree(owner, repo, branch),
    }

# 이 파일을 직접 실행했을 때만 동작
if __name__ == "__main__":
    import json
    import sys

    # URL이 입력되지 않을 시 사용법 안내
    if len(sys.argv) < 2:
        print("Usage: python -m app.github_client <repo_url>")
        sys.exit(1)

    result = scan_repository(sys.argv[1])

    # 파일을 직접 UTF-8로 열어서 씀 : 특수문자 대비
    with open("result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print("result.json 파일로 저장")