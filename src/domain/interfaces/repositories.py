"""Domain layer - Interfaces (Ports)"""

from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities.repository import (
    RepositoryAnalysis,
    RepositoryMetadata,
    SourceFile,
)
from src.domain.value_objects import GitHubURL


class GitHubRepository(ABC):
    """GitHub repository interface (Port)"""
    
    @abstractmethod
    def fetch_metadata(self, url: GitHubURL) -> RepositoryMetadata:
        """Fetch repository metadata"""
        ...
    
    @abstractmethod
    def fetch_file_tree(self, url: GitHubURL) -> dict[str, dict[str, str]]:
        """Fetch repository file tree structure"""
        ...
    
    @abstractmethod
    def fetch_source_files(
        self,
        url: GitHubURL,
        max_files: int = 30
    ) -> list[SourceFile]:
        """Fetch key source files from repository"""
        ...
    
    @abstractmethod
    def fetch_file_content(
        self,
        url: GitHubURL,
        file_path: str
    ) -> Optional[str]:
        """Fetch individual file content"""
        ...


class AIAnalyzer(ABC):
    """AI analyzer interface (Port)"""
    
    @abstractmethod
    def analyze(self, analysis: RepositoryAnalysis) -> str:
        """Analyze repository and return JSON result"""
        ...


class DiagramRenderer(ABC):
    """Diagram renderer interface (Port)"""
    
    @abstractmethod
    def render_erd(self, mermaid_code: str) -> str:
        """Render ERD diagram and return image URL"""
        ...
    
    @abstractmethod
    def render_sequence(self, mermaid_code: str) -> str:
        """Render sequence diagram and return image URL"""
        ...


class CardBuilder(ABC):
    """Adaptive Card builder interface (Port)"""
    
    @abstractmethod
    def build_result_card(
        self,
        repo_url: str,
        api_spec: str,
        erd_image_url: str,
        sequence_image_url: str,
        summary: dict[str, str],
        insights: list[str]
    ) -> dict:
        """Build adaptive card for result"""
        ...
    
    @abstractmethod
    def build_ack_message(self) -> dict:
        """Build acknowledgment message"""
        ...
    
    @abstractmethod
    def build_error_message(self, error: str) -> dict:
        """Build error message"""
    @abstractmethod
    def build_error_message(self, error: str) -> dict:
        """Build error message"""
        ...
    
    @abstractmethod
    def build_download_card(
        self,
        summary: dict[str, str],
        download_url: str,
        document_count: int,
        expires_in_seconds: int,
    ) -> dict:
        """Build adaptive card with download button for ZIP file"""
        ...
