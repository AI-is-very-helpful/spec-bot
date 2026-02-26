"""Unit tests for Domain Entities - RepositoryAnalysis"""

import pytest
from datetime import datetime

from src.domain.entities.repository import (
    FileType,
    RepositoryAnalysis,
    RepositoryMetadata,
    SourceFile,
)
from src.domain.value_objects import GitHubURL


class TestSourceFile:
    """Test cases for SourceFile entity"""
    
    def test_source_file_creation(self) -> None:
        """Test creating a SourceFile"""
        sf = SourceFile(
            path="src/controllers/user.py",
            content="def get_user(): pass",
            file_type=FileType.CONTROLLER
        )
        assert sf.path == "src/controllers/user.py"
        assert sf.file_type == FileType.CONTROLLER
        assert sf.is_key_file is True
    
    def test_source_file_non_key(self) -> None:
        """Test non-key SourceFile"""
        sf = SourceFile(
            path="README.md",
            content="# Readme",
            file_type=FileType.OTHER
        )
        assert sf.is_key_file is False
    
    def test_source_file_file_path_vo(self) -> None:
        """Test SourceFile creates FilePath value object"""
        sf = SourceFile(
            path="src/main.py",
            content="main",
            file_type=FileType.ENTRYPOINT
        )
        assert sf.file_path_vo.value == "src/main.py"
        assert sf.file_path_vo.extension == "py"


class TestRepositoryMetadata:
    """Test cases for RepositoryMetadata entity"""
    
    def test_repository_metadata_creation(self) -> None:
        """Test creating RepositoryMetadata"""
        meta = RepositoryMetadata(
            owner="owner",
            name="repo",
            url="https://github.com/owner/repo",
            language="Python",
            description="A test repo"
        )
        assert meta.owner == "owner"
        assert meta.name == "repo"
        assert meta.language == "Python"
    
    def test_repository_metadata_optional_fields(self) -> None:
        """Test RepositoryMetadata with optional fields"""
        meta = RepositoryMetadata(
            owner="owner",
            name="repo",
            url="https://github.com/owner/repo"
        )
        assert meta.language is None
        assert meta.description is None


class TestRepositoryAnalysis:
    """Test cases for RepositoryAnalysis entity"""
    
    def test_repository_analysis_creation(self) -> None:
        """Test creating RepositoryAnalysis"""
        url = GitHubURL(value="https://github.com/owner/repo")
        meta = RepositoryMetadata(
            owner="owner",
            name="repo",
            url=url.value,
            language="Python"
        )
        
        analysis = RepositoryAnalysis(
            url=url,
            metadata=meta
        )
        
        assert analysis.url == url
        assert analysis.metadata == meta
        assert analysis.analyzed_at is not None
    
    def test_repository_analysis_with_files(self) -> None:
        """Test RepositoryAnalysis with source files"""
        url = GitHubURL(value="https://github.com/owner/repo")
        meta = RepositoryMetadata(
            owner="owner",
            name="repo",
            url=url.value
        )
        
        files = [
            SourceFile(
                path="src/controllers/user.py",
                content="def get_user(): pass",
                file_type=FileType.CONTROLLER
            ),
            SourceFile(
                path="src/services/user.py",
                content="class UserService: pass",
                file_type=FileType.SERVICE
            ),
        ]
        
        analysis = RepositoryAnalysis(
            url=url,
            metadata=meta,
            source_files=files
        )
        
        assert len(analysis.source_files) == 2
        assert analysis.has_sufficient_data is False  # Less than 3
    
    def test_repository_analysis_key_files(self) -> None:
        """Test getting key files"""
        url = GitHubURL(value="https://github.com/owner/repo")
        meta = RepositoryMetadata(
            owner="owner",
            name="repo",
            url=url.value
        )
        
        files = [
            SourceFile(
                path="src/controllers/user.py",
                content="def get_user(): pass",
                file_type=FileType.CONTROLLER
            ),
            SourceFile(
                path="README.md",
                content="Readme",
                file_type=FileType.OTHER
            ),
        ]
        
        analysis = RepositoryAnalysis(
            url=url,
            metadata=meta,
            source_files=files
        )
        
        assert len(analysis.key_files) == 1
        assert analysis.key_files[0].path == "src/controllers/user.py"
    
    def test_has_sufficient_data(self) -> None:
        """Test has_sufficient_data property"""
        url = GitHubURL(value="https://github.com/owner/repo")
        meta = RepositoryMetadata(
            owner="owner",
            name="repo",
            url=url.value
        )
        
        files = [
            SourceFile(
                path=f"src/file{i}.py",
                content=f"content{i}",
                file_type=FileType.OTHER
            )
            for i in range(5)
        ]
        
        analysis = RepositoryAnalysis(
            url=url,
            metadata=meta,
            source_files=files
        )
        
        assert analysis.has_sufficient_data is True
