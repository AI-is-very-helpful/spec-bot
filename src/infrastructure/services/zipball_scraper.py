"""Infrastructure - Zipball Scraper (Memory-based GitHub Repository Download)"""

import io
import logging
import re
import zipfile
from typing import Optional

import requests

from src.domain.entities.repository import (
    FileType,
    RepositoryMetadata,
    SourceFile,
)
from src.domain.value_objects import GitHubURL

logger = logging.getLogger(__name__)

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

# Config file extensions
CONFIG_EXTENSIONS: frozenset[str] = frozenset([
    ".xml", ".gradle", ".gradle.kts", ".yml", ".yaml",
    ".json", ".toml", ".properties", ".env"
])

# Config file names
CONFIG_FILE_NAMES: frozenset[str] = frozenset([
    "pom.xml", "build.gradle", "build.gradle.kts",
    "docker-compose.yml", "docker-compose.yaml", "Dockerfile",
    "requirements.txt", "requirements-dev.txt", "pyproject.toml",
    "setup.py", "setup.cfg", "package.json", "tsconfig.json",
    "application.yml", "application.yaml", "application.properties"
])

# Key file patterns
KEY_FILE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(controller|router|route|handler|endpoint|api)"),
    re.compile(r"(?i)(service|business|logic|usecase)"),
    re.compile(r"(?i)(entity|model|schema|dto|vo|domain)"),
    re.compile(r"(?i)(config|setting)"),
    re.compile(r"(?i)(main|app|server|index|setup)"),
    re.compile(r"(?i)(migration|seeder|database|repository|repo)"),
]

# Max file size (chars)
MAX_FILE_SIZE: int = 5000


class ZipballScraper:
    """GitHub repository scraper using Zipball API (memory-based, no disk I/O)"""
    
    def __init__(self, token: Optional[str] = None) -> None:
        """Initialize scraper
        
        Args:
            token: Optional GitHub personal access token
        """
        self._token = token
        self._session = requests.Session()
        if token:
            self._session.headers["Authorization"] = f"token {token}"
        self._session.headers["Accept"] = "application/vnd.github.v3+json"
    
    def _get_zipball_url(self, owner: str, repo: str, ref: str = "HEAD") -> str:
        """Get zipball URL for repository
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch/tag ref (default: HEAD)
            
        Returns:
            Zipball download URL
        """
        if ref == "HEAD":
            return f"https://api.github.com/repos/{owner}/{repo}/zipball"
        return f"https://api.github.com/repos/{owner}/{repo}/zipball/ref/{ref}"
    
    def _parse_zipball(self, zip_content: bytes) -> list[SourceFile]:
        """Parse zipball content in memory
        
        Args:
            zip_content: Raw zip file bytes
            
        Returns:
            List of SourceFile objects
        """
        files: list[SourceFile] = []
        
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content), 'r') as zf:
                # Get the root directory name (e.g., "owner-repo-branch")
                root_dir = ""
                for name in zf.namelist():
                    if name.endswith("/") and name.count("/") == 1:
                        root_dir = name
                        break
                
                # Extract each file
                for name in zf.namelist():
                    # Skip directories
                    if name.endswith("/"):
                        continue
                    
                    # Skip files outside root directory
                    if root_dir and not name.startswith(root_dir):
                        continue
                    
                    # Get relative path (remove root directory)
                    relative_path = name[len(root_dir):] if root_dir else name
                    if relative_path.startswith("/"):
                        relative_path = relative_path[1:]
                    
                    if not relative_path:
                        continue
                    
                    # Read file content
                    try:
                        content = zf.read(name).decode("utf-8")
                    except UnicodeDecodeError:
                        # Skip binary files
                        continue
                    
                    # Create SourceFile
                    source_file = SourceFile(
                        path=relative_path,
                        content=content,
                        file_type=self._classify_file_type(relative_path),
                    )
                    files.append(source_file)
        
        except zipfile.BadZipFile as e:
            logger.error(f"Invalid zip file: {e}")
            raise ValueError("Failed to parse zipball: invalid zip file")
        
        return files
    
    def _filter_key_files(
        self,
        files: list[SourceFile],
        max_files: int = 30
    ) -> list[SourceFile]:
        """Filter key files for analysis (max 30 files, 5000 chars each)
        
        Args:
            files: List of source files
            max_files: Maximum number of files to return
            
        Returns:
            Filtered list of key source files
        """
        key_files: list[SourceFile] = []
        
        for file in files:
            # Skip non-key files
            if file.file_type == FileType.OTHER:
                continue
            
            # Skip ignored directories
            path_parts = file.path.split("/")
            if any(part in IGNORE_DIRS for part in path_parts):
                continue
            
            # Truncate content
            truncated_content = self._truncate_content(file.content, MAX_FILE_SIZE)
            
            key_files.append(SourceFile(
                path=file.path,
                content=truncated_content,
                file_type=file.file_type,
            ))
            
            if len(key_files) >= max_files:
                break
        
        return key_files
    
    def _truncate_content(self, content: str, max_chars: int = MAX_FILE_SIZE) -> str:
        """Truncate content to max chars
        
        Args:
            content: File content
            max_chars: Maximum characters
            
        Returns:
            Truncated content
        """
        if len(content) <= max_chars:
            return content
        return content[:max_chars]
    
    def _is_key_file(self, path: str) -> bool:
        """Check if file is a key file
        
        Args:
            path: File path
            
        Returns:
            True if key file
        """
        name = path.split("/")[-1]
        ext = f".{name.split('.')[-1]}" if "." in name else ""
        
        # Always include config file names
        if name in CONFIG_FILE_NAMES:
            return True
        
        # Check extensions
        if ext not in CODE_EXTENSIONS and ext not in CONFIG_EXTENSIONS:
            return False
        
        # Check ignore directories
        for ignore in IGNORE_DIRS:
            if f"/{ignore}/" in path or path.startswith(f"{ignore}/"):
                return False
        
        # Check key patterns
        for pattern in KEY_FILE_PATTERNS:
            if pattern.search(name):
                return True
        
        return False
    
    def _classify_file_type(self, path: str) -> FileType:
        """Classify file type based on path
        
        Args:
            path: File path
            
        Returns:
            FileType classification
        """
        path_lower = path.lower()
        
        if re.search(r"(controller|router|route|handler|endpoint|api)", path_lower):
            return FileType.CONTROLLER
        elif re.search(r"(service|business|logic|usecase)", path_lower):
            return FileType.SERVICE
        elif re.search(r"(entity|model|schema|dto|vo|domain)", path_lower):
            return FileType.ENTITY
        elif re.search(r"(config|setting)", path_lower):
            return FileType.CONFIG
        elif re.search(r"(main|app|server|index|setup)", path_lower):
            return FileType.ENTRYPOINT
        elif re.search(r"(migration|seeder|database|repository|repo)", path_lower):
            return FileType.REPOSITORY
        
        return FileType.OTHER
    
    def fetch_repository(
        self,
        owner: str,
        repo: str,
        ref: str = "HEAD",
        max_files: int = 30
    ) -> list[SourceFile]:
        """Fetch repository using Zipball API (memory-based)
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch/tag ref (default: HEAD)
            max_files: Maximum number of files to return
            
        Returns:
            List of key source files
            
        Raises:
            Exception: If rate limited or other errors
        """
        # Get zipball URL
        url = self._get_zipball_url(owner, repo, ref)
        
        logger.info(f"Fetching zipball: {url}")
        
        # Download zipball
        response = self._session.get(url, timeout=60)
        
        if response.status_code == 403:
            rate_limit = response.headers.get("X-RateLimit-Remaining", "0")
            if rate_limit == "0":
                reset_time = response.headers.get("X-RateLimit-Reset", "unknown")
                raise Exception(f"GitHub API rate limited. Resets at: {reset_time}")
            raise Exception(f"GitHub API error: 403 Forbidden")
        
        if response.status_code == 404:
            raise Exception(f"Repository not found: {owner}/{repo}")
        
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code}")
        
        # Parse zipball in memory
        files = self._parse_zipball(response.content)
        
        logger.info(f"Parsed {len(files)} files from zipball")
        
        # Filter key files
        key_files = self._filter_key_files(files, max_files)
        
        logger.info(f"Filtered to {len(key_files)} key files")
        
        return key_files
    
    def fetch_metadata(self, url: GitHubURL) -> RepositoryMetadata:
        """Fetch repository metadata
        
        Args:
            url: GitHub URL
            
        Returns:
            Repository metadata
        """
        api_url = f"https://api.github.com/repos/{url.full_name}"
        
        response = self._session.get(api_url, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to fetch metadata: {response.status_code}")
        
        data = response.json()
        
        return RepositoryMetadata(
            owner=data["owner"]["login"],
            name=data["name"],
            url=url.value,
            language=data.get("language"),
            description=data.get("description"),
        )
