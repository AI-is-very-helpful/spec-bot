"""Domain layer - Value Objects"""

from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass(frozen=True)
class GitHubURL:
    """GitHub Repository URL Value Object"""
    value: str
    
    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("GitHub URL cannot be empty")
        
        parsed = urlparse(self.value)
        if parsed.netloc != "github.com":
            raise ValueError(f"Invalid GitHub URL: {self.value}")
        
        path_parts = parsed.path.strip("/").split("/")
        if len(path_parts) < 2:
            raise ValueError(f"Invalid GitHub repository path: {self.value}")
    
    @property
    def owner(self) -> str:
        """Extract owner from URL"""
        path_parts = self.value.strip("/").split("/")
        return path_parts[-2]
    
    @property
    def repo_name(self) -> str:
        """Extract repository name from URL"""
        path_parts = self.value.strip("/").split("/")
        repo = path_parts[-1]
        # Remove .git suffix if present
        return repo.replace(".git", "")
    
    @property
    def full_name(self) -> str:
        """Get owner/repo format"""
        return f"{self.owner}/{self.repo_name}"


@dataclass(frozen=True)
class FilePath:
    """File path Value Object"""
    value: str
    
    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("File path cannot be empty")
    
    @property
    def extension(self) -> str:
        """Get file extension"""
        if "." in self.value:
            return self.value.rsplit(".", 1)[1]
        return ""
    
    @property
    def name(self) -> str:
        """Get file name"""
        return self.value.split("/")[-1]
    
    @property
    def directory(self) -> str:
        """Get directory path"""
        parts = self.value.rsplit("/", 1)
        return parts[0] if len(parts) > 1 else ""


@dataclass(frozen=True)
class SourceCode:
    """Source code content Value Object"""
    content: str
    file_path: FilePath
    
    def __post_init__(self) -> None:
        if not self.content:
            raise ValueError("Source code content cannot be empty")
    
    @property
    def truncated(self) -> "SourceCode":
        """Return truncated source code (max 5000 chars)"""
        if len(self.content) <= 5000:
            return self
        return SourceCode(
            content=self.content[:5000],
            file_path=self.file_path
        )
