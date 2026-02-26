"""GitHub Repository Scraper - 핵심 파일 선별 추출 모듈"""

import re
import logging
from dataclasses import dataclass
from typing import Optional

import requests
from github import Github
from github.Repository import Repository
from github.ContentFile import ContentFile

logger = logging.getLogger(__name__)


# 핵심 파일 패턴 (프로젝트 아키텍처 결정 파일)
KEY_FILE_PATTERNS = [
    # Controllers / Routes
    r"(?i)(controller|router|route|handler|endpoint|api)",
    # Services / Business Logic
    r"(?i)(service|business|logic|usecase)",
    # Entities / Models / Schemas
    r"(?i)(entity|model|schema|dto|vo|domain)",
    # Configuration
    r"(?i)(config|setting)",
    # Main entry points
    r"(?i)(main|app|server|index|setup)",
    # Database / ORM
    r"(?i)(migration|seeder|database|repository|repo)",
]

# 무시할 디렉토리 패턴
IGNORE_DIRS = [
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "vendor", "target",
    ".github", ".vscode", "docs", "test", "tests"
]

# 파일 확장자 필터
CODE_EXTENSIONS = [
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go",
    ".rb", ".php", ".cs", ".rs", ".swift", ".kt", ".scala"
]


@dataclass
class FileContent:
    """추출된 파일 정보"""
    path: str
    content: str
    file_type: str  # controller, service, entity, config, etc.


@dataclass
class RepositoryAnalysis:
    """레포지토리 분석 결과"""
    owner: str
    repo_name: str
    url: str
    files: list[FileContent]
    file_tree: dict  # 디렉토리 구조
    language: Optional[str]
    description: Optional[str]


class GitHubScraper:
    """GitHub 레포지토리에서 핵심 파일 추출"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers["Authorization"] = f"token {token}"
        self.session.headers["Accept"] = "application/vnd.github.v3+json"
        
        if token:
            self.github = Github(token)
        else:
            self.github = Github()
    
    def parse_github_url(self, url: str) -> tuple[str, str]:
        """GitHub URL에서 owner와 repo 이름 추출"""
        # https://github.com/owner/repo 또는 https://github.com/owner/repo.git
        pattern = r"github\.com[/:]([^/]+)/([^/.]+)"
        match = re.search(pattern, url)
        
        if not match:
            raise ValueError(f"Invalid GitHub URL: {url}")
        
        return match.group(1), match.group(2)
    
    def is_key_file(self, path: str, name: str) -> bool:
        """핵심 파일인지 판단"""
        # 확장자 확인
        ext = "." + path.split(".")[-1] if "." in path else ""
        if ext.lower() not in CODE_EXTENSIONS and ext:
            return False
        
        # 디렉토리 무시
        for ignore_dir in IGNORE_DIRS:
            if f"/{ignore_dir}/" in path or path.startswith(ignore_dir + "/"):
                return False
        
        # 패턴 매칭
        for pattern in KEY_FILE_PATTERNS:
            if re.search(pattern, name):
                return True
        
        return False
    
    def get_file_type(self, path: str) -> str:
        """파일 타입 분류"""
        path_lower = path.lower()
        
        if re.search(r"(controller|router|route|handler|endpoint|api)", path_lower):
            return "controller"
        elif re.search(r"(service|business|logic|usecase)", path_lower):
            return "service"
        elif re.search(r"(entity|model|schema|dto|vo|domain)", path_lower):
            return "entity"
        elif re.search(r"(config|setting)", path_lower):
            return "config"
        elif re.search(r"(main|app|server|index|setup)", path_lower):
            return "entrypoint"
        elif re.search(r"(migration|seeder|database|repository|repo)", path_lower):
            return "repository"
        
        return "other"
    
    def fetch_file_content(self, owner: str, repo_name: str, path: str) -> Optional[str]:
        """개별 파일 내용 가져오기"""
        try:
            url = f"https://api.github.com/repos/{owner}/{repo_name}/contents/{path}"
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get("encoding") == "base64":
                import base64
                content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
                return content
            return data.get("content", "")
        except Exception as e:
            logger.warning(f"Failed to fetch file {path}: {e}")
            return None
    
    def build_file_tree(self, repo: Repository) -> dict:
        """레포지토리 파일 트리 구축 (최상위 2단계만)"""
        tree = {}
        try:
            contents = repo.get_contents("")
            for content in contents:
                if content.type == "dir" and content.name not in IGNORE_DIRS:
                    tree[content.name] = {}
                    try:
                        sub_contents = repo.get_contents(content.name)
                        for sub in sub_contents[:10]:  # 각 디렉토리 최대 10개 파일
                            if sub.type == "file":
                                tree[content.name][sub.name] = sub.path
                    except:
                        pass
                elif content.type == "file":
                    tree[content.name] = content.path
        except Exception as e:
            logger.warning(f"Failed to build file tree: {e}")
        
        return tree
    
    def scrape(self, github_url: str) -> RepositoryAnalysis:
        """레포지토리 스크래핑 실행"""
        owner, repo_name = self.parse_github_url(github_url)
        logger.info(f"Scraping repository: {owner}/{repo_name}")
        
        # 레포지토리 정보 가져오기
        repo = self.github.get_repo(f"{owner}/{repo_name}")
        
        language = repo.language
        description = repo.description
        
        # 파일 트리 구축
        file_tree = self.build_file_tree(repo)
        
        # 핵심 파일 추출
        key_files: list[FileContent] = []
        
        try:
            # 재귀적으로 파일 탐색 (깊이 제한)
            contents = repo.get_contents("")
            stack = list(contents)
            visited_paths = set()
            
            while stack and len(key_files) < 30:  # 최대 30개 파일
                content = stack.pop()
                
                if content.path in visited_paths:
                    continue
                visited_paths.add(content.path)
                
                if content.type == "dir":
                    if content.name in IGNORE_DIRS:
                        continue
                    try:
                        stack.extend(repo.get_contents(content.path))
                    except:
                        pass
                else:
                    # 핵심 파일인지 확인
                    if self.is_key_file(content.path, content.name):
                        file_content = self.fetch_file_content(owner, repo_name, content.path)
                        if file_content:
                            key_files.append(FileContent(
                                path=content.path,
                                content=file_content[:5000],  # 파일당 최대 5000자
                                file_type=self.get_file_type(content.path)
                            ))
                            logger.info(f"Found key file: {content.path} ({len(file_content)} chars)")
        
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
        
        return RepositoryAnalysis(
            owner=owner,
            repo_name=repo_name,
            url=github_url,
            files=key_files,
            file_tree=file_tree,
            language=language,
            description=description
        )
