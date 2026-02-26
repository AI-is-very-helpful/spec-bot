"""Unit tests for Application DTOs"""

import pytest
from pydantic import ValidationError

from src.application.dto.repository import (
    AnalyzeRepositoryInput,
    AnalyzeRepositoryOutput,
)


class TestAnalyzeRepositoryInput:
    """Test cases for AnalyzeRepositoryInput DTO"""
    
    def test_valid_input(self) -> None:
        """Test valid input"""
        dto = AnalyzeRepositoryInput(github_url="https://github.com/owner/repo")
        assert dto.github_url == "https://github.com/owner/repo"
    
    def test_input_with_trailing_slash(self) -> None:
        """Test input with trailing slash is stripped"""
        dto = AnalyzeRepositoryInput(github_url="https://github.com/owner/repo/")
        assert dto.github_url == "https://github.com/owner/repo"
    
    def test_input_with_http(self) -> None:
        """Test HTTP URL"""
        dto = AnalyzeRepositoryInput(github_url="http://github.com/owner/repo")
        assert dto.github_url == "http://github.com/owner/repo"
    
    def test_invalid_empty_url(self) -> None:
        """Test empty URL raises error"""
        with pytest.raises(ValidationError):
            AnalyzeRepositoryInput(github_url="")
    
    def test_invalid_non_github_url(self) -> None:
        """Test non-GitHub URL raises error"""
        with pytest.raises(ValidationError, match="Invalid GitHub URL"):
            AnalyzeRepositoryInput(github_url="https://gitlab.com/owner/repo")
    
    def test_input_strips_whitespace(self) -> None:
        """Test whitespace is stripped"""
        dto = AnalyzeRepositoryInput(github_url="  https://github.com/owner/repo  ")
        assert dto.github_url == "https://github.com/owner/repo"


class TestAnalyzeRepositoryOutput:
    """Test cases for AnalyzeRepositoryOutput DTO"""
    
    def test_valid_output(self) -> None:
        """Test valid output"""
        dto = AnalyzeRepositoryOutput(
            card={"type": "AdaptiveCard"},
            api_spec="# API Spec",
            erd_image_url="https://mermaid.ink/img/erd",
            sequence_image_url="https://mermaid.ink/img/seq",
            summary={"name": "Test", "purpose": "Test project"},
            insights=["Insight 1", "Insight 2"]
        )
        assert dto.api_spec == "# API Spec"
        assert len(dto.insights) == 2
    
    def test_output_with_empty_insights(self) -> None:
        """Test output with empty insights"""
        dto = AnalyzeRepositoryOutput(
            card={},
            api_spec="",
            erd_image_url="",
            sequence_image_url="",
            summary={},
            insights=[]
        )
        assert len(dto.insights) == 0
