"""Unit tests for Teams Bot Service"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from src.infrastructure.services.teams_bot import TeamsBotService, MessageFactory


class TestMessageFactory:
    """Test cases for MessageFactory"""
    
    def test_create_ack_message(self) -> None:
        """Test creating ACK message"""
        msg = MessageFactory.create_ack_message()
        assert msg["type"] == "message"
        assert "분석을 시작합니다" in msg["text"]
        assert "1~2분" in msg["text"]
    
    def test_create_error_message(self) -> None:
        """Test creating error message"""
        msg = MessageFactory.create_error_message("Test error")
        assert msg["type"] == "message"
        assert "Test error" in msg["text"]
        assert "오류가 발생했습니다" in msg["text"]
    
    def test_create_help_message(self) -> None:
        """Test creating help message"""
        msg = MessageFactory.create_help_message()
        assert msg["type"] == "message"
        assert "Spec Bot 사용법" in msg["text"]
    
    def test_create_github_not_found_message(self) -> None:
        """Test creating github not found message"""
        msg = MessageFactory.create_github_not_found_message()
        assert msg["type"] == "message"
        assert "GitHub 레포지토리 URL" in msg["text"]


class TestTeamsBotService:
    """Test cases for TeamsBotService"""
    
    def test_extract_github_url_valid(self) -> None:
        """Test extracting valid GitHub URL"""
        service = TeamsBotService(
            app_id="test_id",
            app_password="test_password"
        )
        
        url = service.extract_github_url("Check this https://github.com/owner/repo please")
        assert url == "https://github.com/owner/repo"
    
    def test_extract_github_url_with_trailing_slash(self) -> None:
        """Test extracting URL with trailing slash"""
        service = TeamsBotService(
            app_id="test_id",
            app_password="test_password"
        )
        
        url = service.extract_github_url("https://github.com/owner/repo/")
        assert url == "https://github.com/owner/repo"
    
    def test_extract_github_url_not_found(self) -> None:
        """Test extracting URL when not present"""
        service = TeamsBotService(
            app_id="test_id",
            app_password="test_password"
        )
        
        url = service.extract_github_url("Hello world")
        assert url is None
    
    def test_extract_github_url_gitlab_ignored(self) -> None:
        """Test that non-GitHub URLs are ignored"""
        service = TeamsBotService(
            app_id="test_id",
            app_password="test_password"
        )
        
        url = service.extract_github_url("https://gitlab.com/owner/repo")
        assert url is None
    
    def test_extract_github_url_case_insensitive(self) -> None:
        """Test case insensitive URL extraction"""
        service = TeamsBotService(
            app_id="test_id",
            app_password="test_password"
        )
        
        url = service.extract_github_url("HTTPS://GITHUB.COM/OWNER/REPO")
        assert url is not None
        assert "github.com" in url.lower()
    
    def test_extract_github_url_with_mention(self) -> None:
        """Test extracting URL with bot mention"""
        service = TeamsBotService(
            app_id="test_id",
            app_password="test_password"
        )
        
        url = service.extract_github_url("@SpecBot https://github.com/owner/repo")
        assert url == "https://github.com/owner/repo"
    
    def test_is_help_command(self) -> None:
        """Test help command detection"""
        service = TeamsBotService(
            app_id="test_id",
            app_password="test_password"
        )
        
        assert service.is_help_command("help") is True
        assert service.is_help_command("/help") is True
        assert service.is_help_command("도움말") is True
        assert service.is_help_command("HELP") is True
        assert service.is_help_command("Hello") is False
    
    def test_service_initialization(self) -> None:
        """Test service initialization"""
        service = TeamsBotService(
            app_id="test_app_id",
            app_password="test_password"
        )
        
        assert service._app_id == "test_app_id"
        assert service._app_password == "test_password"
    
    def test_service_initialization_without_credentials(self) -> None:
        """Test service initialization without credentials"""
        service = TeamsBotService()
        
        assert service._app_id == ""
        assert service._app_password == ""
