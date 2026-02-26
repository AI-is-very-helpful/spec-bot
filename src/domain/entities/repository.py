"""Domain layer - Entities"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

from src.domain.value_objects import GitHubURL, FilePath, SourceCode


class FileType(Enum):
    """File type classification"""
    CONTROLLER = "controller"
    SERVICE = "service"
    ENTITY = "entity"
    CONFIG = "config"
    ENTRYPOINT = "entrypoint"
    REPOSITORY = "repository"
    OTHER = "other"


@dataclass(frozen=True)
class SourceFile:
    """Source file entity"""
    path: str
    content: str
    file_type: FileType
    
    @property
    def file_path_vo(self) -> FilePath:
        return FilePath(value=self.path)
    
    @property
    def source_code_vo(self) -> SourceCode:
        return SourceCode(
            content=self.content[:5000],  # Truncate for safety
            file_path=FilePath(value=self.path)
        )
    
    @property
    def is_key_file(self) -> bool:
        """Check if this is a key architecture file"""
        return self.file_type != FileType.OTHER


@dataclass(frozen=True)
class RepositoryMetadata:
    """Repository metadata entity"""
    owner: str
    name: str
    url: str
    language: Optional[str] = None
    description: Optional[str] = None


@dataclass
class RepositoryAnalysis:
    """Repository analysis entity (not frozen due to mutable state)"""
    url: GitHubURL
    metadata: RepositoryMetadata
    source_files: list[SourceFile] = field(default_factory=list)
    file_tree: dict[str, dict[str, str]] = field(default_factory=dict)
    analyzed_at: Optional[datetime] = None
    
    def __post_init__(self) -> None:
        if self.analyzed_at is None:
            object.__setattr__(self, 'analyzed_at', datetime.utcnow())
    
    @property
    def key_files(self) -> list[SourceFile]:
        """Get only key architecture files"""
        return [f for f in self.source_files if f.is_key_file]
    
    @property
    def has_sufficient_data(self) -> bool:
        """Check if analysis has enough data"""
        return len(self.source_files) >= 3


@dataclass(frozen=True)
class ProjectSummary:
    """Project summary value object"""
    name: str
    purpose: str
    tech_stack: tuple[str, ...]
    architecture: str
    folder_structure: tuple[str, ...]


@dataclass(frozen=True)
class APIEndpoint:
    """API endpoint value object"""
    path: str
    method: str
    summary: str
    description: Optional[str] = None
    request_params: Optional[tuple[str, ...]] = None
    request_body: Optional[str] = None
    response: Optional[str] = None


@dataclass(frozen=True)
class AnalysisResult:
    """Analysis result value object"""
    project_summary: ProjectSummary
    api_spec: str
    erd_code: str
    sequence_code: str
    key_insights: tuple[str, ...]
