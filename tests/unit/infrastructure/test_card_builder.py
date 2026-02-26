"""Unit tests for Infrastructure - Card Builder"""

import pytest
from unittest.mock import Mock

from src.infrastructure.services.card import TeamsCardBuilder


class TestTeamsCardBuilder:
    """Test cases for TeamsCardBuilder"""
    
    def test_build_result_card_structure(self) -> None:
        """Test result card has correct structure"""
        builder = TeamsCardBuilder()
        
        card = builder.build_result_card(
            repo_url="https://github.com/owner/repo",
            api_spec="# API Spec",
            erd_image_url="https://mermaid.ink/img/erd",
            sequence_image_url="https://mermaid.ink/img/seq",
            summary={
                "name": "TestRepo",
                "purpose": "A test repository",
                "architecture": "MVC",
                "tech_stack": ["Python", "FastAPI"]
            },
            insights=["Insight 1", "Insight 2", "Insight 3"]
        )
        
        assert card["$schema"] == "http://adaptivecards.io/schemas/adaptive-card.json"
        assert card["type"] == "AdaptiveCard"
        assert card["version"] == "1.4"
        assert "body" in card
        assert "actions" in card
    
    def test_build_ack_message(self) -> None:
        """Test acknowledgment message"""
        builder = TeamsCardBuilder()
        
        msg = builder.build_ack_message()
        
        assert msg["type"] == "message"
        assert "분석을 시작합니다" in msg["text"]
    
    def test_build_error_message(self) -> None:
        """Test error message"""
        builder = TeamsCardBuilder()
        
        msg = builder.build_error_message("Test error")
        
        assert msg["type"] == "message"
        assert "Test error" in msg["text"]
        assert "오류가 발생했습니다" in msg["text"]
    
    def test_build_help_message(self) -> None:
        """Test help message"""
        builder = TeamsCardBuilder()
        
        msg = builder.build_help_message()
        
        assert msg["type"] == "message"
        assert "Spec Bot 사용법" in msg["text"]
    
    def test_result_card_contains_repo_url(self) -> None:
        """Test result card contains GitHub URL"""
        builder = TeamsCardBuilder()
        
        card = builder.build_result_card(
            repo_url="https://github.com/owner/repo",
            api_spec="",
            erd_image_url="",
            sequence_image_url="",
            summary={},
            insights=[]
        )
        
        # Check URL in card body
        url_found = False
        for item in card["body"]:
            if item.get("text", "").startswith("["):
                if "github.com/owner/repo" in item["text"]:
                    url_found = True
                    break
        
        assert url_found or "owner/repo" in str(card)
