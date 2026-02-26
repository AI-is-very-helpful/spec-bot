"""Infrastructure - GitHub Repository Implementation"""

import re
from typing import Optional

import requests
from github import Github
from github.Repository import Repository

from src.domain.entities.repository import (
    FileType,
    RepositoryAnalysis,
    RepositoryMetadata,
    SourceFile,
)
from src.domain.interfaces.repositories import GitHubRepository
from src.domain.value_objects import GitHubURL

# Ignore directories
IGNORE_DIRS: frozenset[str] = frozenset([
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".nuxt", "vendor", "target",
    ".github", ".vscode", "docs", "test", "tests"
])

# Code file extensions
CODE_EXTENSIONS: frozenset[str] = frozenset([
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go",
    ".rb", ".php", ".cs", ".rs", ".swift", ".kt", ".scala"
])

# Config file extensions (always include these)
CONFIG_EXTENSIONS: frozenset[str] = frozenset([
    ".xml", ".gradle", ".gradle.kts", ".yml", ".yaml",
    ".json", ".toml", ".properties", ".env"
])

# Build/Config file names (always include these)
CONFIG_FILE_NAMES: frozenset[str] = frozenset([
    "pom.xml", "build.gradle", "build.gradle.kts",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    "requirements.txt", "requirements-dev.txt", "pyproject.toml",
    "setup.py", "setup.cfg", "package.json", "tsconfig.json",
    "application.yml", "application.yaml", "application.properties"
])

# Key file patterns — 경로 전체(path)에 대해 매칭 (폴더명/파일명 모두)
# 예: entity/User.py, domain/aggregates/Order.py, src/api/handlers/ 등 구조 다양성 반영
KEY_FILE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(controller|router|route|handler|endpoint|api)"),
    re.compile(r"(?i)(service|business|logic|usecase|application)"),
    re.compile(r"(?i)(entity|entities|model|models|schema|dto|vo|domain|aggregate|value_object)"),
    re.compile(r"(?i)(config|setting|settings)"),
    re.compile(r"(?i)(main|app|server|index|setup|bootstrap)"),
    re.compile(r"(?i)(migration|seeder|database|repository|repo|persistence)"),
    re.compile(r"(?i)(command|query|adapter|port|infrastructure)"),
]


class PyGitHubRepository(GitHubRepository):
    """PyGithub implementation of GitHubRepository"""
    
    def __init__(self, token: Optional[str] = None) -> None:
        self._token = token
        self._session = requests.Session()
        if token:
            self._session.headers["Authorization"] = f"token {token}"
        self._session.headers["Accept"] = "application/vnd.github.v3+json"
        
        self._github = Github(token) if token else Github()
    
    def fetch_metadata(self, url: GitHubURL) -> RepositoryMetadata:
        repo = self._github.get_repo(url.full_name)
        return RepositoryMetadata(
            owner=repo.owner.login,
            name=repo.name,
            url=url.value,
            language=repo.language,
            description=repo.description,
        )
    
    def fetch_file_tree(self, url: GitHubURL) -> dict[str, dict[str, str]]:
        repo = self._github.get_repo(url.full_name)
        tree: dict[str, dict[str, str]] = {}
        
        try:
            contents = repo.get_contents("")
            for content in contents:
                if content.type == "dir" and content.name not in IGNORE_DIRS:
                    tree[content.name] = {}
                    try:
                        sub_contents = repo.get_contents(content.name)
                        for sub in sub_contents[:10]:
                            if sub.type == "file":
                                tree[content.name][sub.name] = sub.path
                    except Exception:
                        pass
                elif content.type == "file":
                    tree[content.name] = content.path
        except Exception:
            pass
        
        return tree
    
    def fetch_source_files(
        self,
        url: GitHubURL,
        max_files: int = 30
    ) -> list[SourceFile]:
        repo = self._github.get_repo(url.full_name)
        source_files: list[SourceFile] = []
        visited_paths: set[str] = set()
        
        try:
            contents = repo.get_contents("")
            stack = list(contents)
            
            while stack and len(source_files) < max_files:
                content = stack.pop()
                
                if content.path in visited_paths:
                    continue
                visited_paths.add(content.path)
                
                if content.type == "dir":
                    if content.name in IGNORE_DIRS:
                        continue
                    try:
                        stack.extend(repo.get_contents(content.path))
                    except Exception:
                        pass
                else:
                    if self._is_key_file(content.path):
                        file_content = self.fetch_file_content(url, content.path)
                        if file_content:
                            source_files.append(SourceFile(
                                path=content.path,
                                content=file_content[:5000],
                                file_type=self._classify_file_type(content.path),
                            ))
        
        except Exception:
            pass
        
        return source_files
    
    def fetch_file_content(
        self,
        url: GitHubURL,
        file_path: str
    ) -> Optional[str]:
        try:
            repo = self._github.get_repo(url.full_name)
            content = repo.get_contents(file_path)
            if content.encoding == "base64":
                import base64
                return base64.b64decode(content.content).decode("utf-8")
            return content.content
        except Exception:
            return None
    
    def _is_key_file(self, path: str) -> bool:
        name = path.split("/")[-1]
        ext = f".{name.split('.')[-1]}" if "." in name else ""

        # Always include config file names (pom.xml, build.gradle, etc.)
        if name in CONFIG_FILE_NAMES:
            return True

        if ext not in CONFIG_EXTENSIONS and ext not in CODE_EXTENSIONS:
            return False

        for ignore in IGNORE_DIRS:
            if f"/{ignore}/" in path or path.startswith(f"{ignore}/"):
                return False

        # 경로 전체로 매칭 — 폴더명이 entity/ domain/ 등이면 파일명이 User.py여도 포함
        path_lower = path.lower()
        for pattern in KEY_FILE_PATTERNS:
            if pattern.search(path_lower):
                return True

        # 설정 확장자 파일은 패턴 없이 포함 (application.yml 등)
        if ext in CONFIG_EXTENSIONS:
            return True

        return False
    
    def _classify_file_type(self, path: str) -> FileType:
        path_lower = path.lower()
        if re.search(r"(controller|router|route|handler|endpoint|api)", path_lower):
            return FileType.CONTROLLER
        if re.search(r"(service|business|logic|usecase|application)", path_lower):
            return FileType.SERVICE
        if re.search(r"(entity|model|schema|dto|vo|domain|aggregate|value_object)", path_lower):
            return FileType.ENTITY
        if re.search(r"(config|setting)", path_lower):
            return FileType.CONFIG
        if re.search(r"(main|app|server|index|setup)", path_lower):
            return FileType.ENTRYPOINT
        if re.search(r"(migration|seeder|database|repository|repo|persistence)", path_lower):
            return FileType.REPOSITORY
        return FileType.OTHER
