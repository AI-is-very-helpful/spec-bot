"""Unit tests for Multi-Document Pydantic Models"""

import pytest
from pydantic import ValidationError

from src.application.dto.repository import (
    AnalyzeRepositoryInput,
    AnalyzeRepositoryOutput,
)
from src.application.dto.multidoc import (
    MultiDocumentAnalysisInput,
    MultiDocumentAnalysisOutput,
    DocumentPackage,
)


class TestMultiDocumentAnalysisInput:
    """Test cases for MultiDocumentAnalysisInput DTO"""
    
    def test_valid_input(self) -> None:
        """Test valid input with GitHub URL"""
        dto = MultiDocumentAnalysisInput(github_url="https://github.com/owner/repo")
        assert dto.github_url == "https://github.com/owner/repo"
    
    def test_invalid_url(self) -> None:
        """Test invalid URL raises error"""
        with pytest.raises(ValidationError, match="Invalid GitHub URL"):
            MultiDocumentAnalysisInput(github_url="https://gitlab.com/owner/repo")


class TestMultiDocumentAnalysisOutput:
    """Test cases for MultiDocumentAnalysisOutput DTO"""
    
    def test_valid_output(self) -> None:
        """Test valid output with all 7 documents"""
        dto = MultiDocumentAnalysisOutput(
            zip_blob_url="https://storage.blob.core.windows.net/container/doc.zip?sv=2021-06",
            summary={
                "name": "TestRepo",
                "purpose": "Test project",
                "tech_stack": ["Python", "FastAPI"],
                "architecture": "MVC"
            },
            document_count=7,
            expires_in_seconds=86400
        )
        
        assert dto.zip_blob_url.startswith("https://")
        assert dto.document_count == 7
        assert dto.expires_in_seconds == 86400  # 24 hours
    
    def test_output_default_expiry(self) -> None:
        """Test default expiry is 24 hours"""
        dto = MultiDocumentAnalysisOutput(
            zip_blob_url="https://example.com/blob",
            summary={"name": "Test"},
            document_count=7
        )
        assert dto.expires_in_seconds == 86400


class TestDocumentPackage:
    """Test cases for DocumentPackage DTO"""
    
    def test_valid_package(self) -> None:
        """Test valid document package"""
        dto = DocumentPackage(
            api_spec="# API Spec",
            erd="# ERD",
            sequence="# Sequence",
            architecture="# Architecture",
            dependencies="# Dependencies",
            structure="# Structure",
            state_machine="# State Machine"
        )
        
        assert dto.api_spec == "# API Spec"
        assert dto.erd == "# ERD"
        assert dto.sequence == "# Sequence"
        assert dto.architecture == "# Architecture"
        assert dto.dependencies == "# Dependencies"
        assert dto.structure == "# Structure"
        assert dto.state_machine == "# State Machine"
        assert len(dto) == 7
    
    def test_package_keys(self) -> None:
        """Test document package has correct keys"""
        package = DocumentPackage(
            api_spec="",
            erd="",
            sequence="",
            architecture="",
            dependencies="",
            structure="",
            state_machine=""
        )
        
        keys = list(package.keys())
        expected = [
            "api_spec.md",
            "erd.md",
            "sequence.md",
            "architecture.md",
            "dependencies.md",
            "structure.md",
            "state_machine.md"
        ]
        
        assert keys == expected
