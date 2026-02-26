"""Unit tests for Domain Value Objects - GitHubURL"""

import pytest
from pydantic import ValidationError

from src.domain.value_objects import GitHubURL


class TestGitHubURL:
    """Test cases for GitHubURL value object"""
    
    def test_valid_github_url_https(self) -> None:
        """Test valid HTTPS GitHub URL"""
        url = GitHubURL(value="https://github.com/owner/repo")
        assert url.value == "https://github.com/owner/repo"
        assert url.owner == "owner"
        assert url.repo_name == "repo"
        assert url.full_name == "owner/repo"
    
    def test_valid_github_url_http(self) -> None:
        """Test valid HTTP GitHub URL"""
        url = GitHubURL(value="http://github.com/owner/repo")
        assert url.owner == "owner"
        assert url.repo_name == "repo"
    
    def test_valid_github_url_with_git_suffix(self) -> None:
        """Test URL with .git suffix is handled"""
        url = GitHubURL(value="https://github.com/owner/repo.git")
        assert url.repo_name == "repo"
    
    def test_valid_github_url_with_trailing_slash(self) -> None:
        """Test URL with trailing slash"""
        url = GitHubURL(value="https://github.com/owner/repo/")
        assert url.repo_name == "repo"
    
    def test_invalid_url_empty(self) -> None:
        """Test empty URL raises error"""
        with pytest.raises(ValueError, match="cannot be empty"):
            GitHubURL(value="")
    
    def test_invalid_url_not_github(self) -> None:
        """Test non-GitHub URL raises error"""
        with pytest.raises(ValueError, match="Invalid GitHub URL"):
            GitHubURL(value="https://gitlab.com/owner/repo")
    
    def test_invalid_url_missing_repo(self) -> None:
        """Test URL missing repository name raises error"""
        with pytest.raises(ValueError, match="Invalid GitHub repository path"):
            GitHubURL(value="https://github.com/owner")
    
    def test_url_immutable(self) -> None:
        """Test GitHubURL is immutable"""
        url = GitHubURL(value="https://github.com/owner/repo")
        with pytest.raises(AttributeError):
            url.value = "https://github.com/new/repo"  # type: ignore[assignment]
    
    def test_url_equality(self) -> None:
        """Test GitHubURL equality"""
        url1 = GitHubURL(value="https://github.com/owner/repo")
        url2 = GitHubURL(value="https://github.com/owner/repo")
        assert url1 == url2
