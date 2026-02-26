"""Unit tests for Infrastructure - Mermaid Renderer"""

import pytest
from unittest.mock import Mock, patch

from src.infrastructure.services.mermaid import MermaidInkRenderer


class TestMermaidInkRenderer:
    """Test cases for MermaidInkRenderer"""
    
    def test_encode_basic(self) -> None:
        """Test basic encoding"""
        code = "graph TD; A-->B;"
        encoded = MermaidInkRenderer._encode(code)
        assert "graph" in encoded
        assert "TD" in encoded
    
    def test_encode_with_spaces(self) -> None:
        """Test encoding with spaces is handled"""
        code = "  graph TD;  A-->B;  "
        encoded = MermaidInkRenderer._encode(code)
        assert encoded.startswith("graph")
    
    def test_encode_special_chars(self) -> None:
        """Test encoding with special characters"""
        code = "erDiagram\n  USER ||--o{ ORDER : places"
        encoded = MermaidInkRenderer._encode(code)
        assert "erDiagram" in encoded
    
    def test_render_erd(self) -> None:
        """Test ERD rendering returns URL"""
        renderer = MermaidInkRenderer()
        
        with patch("requests.head") as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://mermaid.ink/img/encoded"
            mock_head.return_value = mock_response
            
            result = renderer.render_erd("erDiagram\n  A ||--|| B")
            
            assert "mermaid.ink" in result
            mock_head.assert_called_once()
    
    def test_render_erd_fallback(self) -> None:
        """Test ERD rendering fallback on failure"""
        renderer = MermaidInkRenderer()
        
        with patch("requests.head") as mock_head:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_head.return_value = mock_response
            
            result = renderer.render_erd("erDiagram\n  A ||--|| B")
            
            assert "mermaid.ink" in result
    
    def test_render_sequence(self) -> None:
        """Test sequence diagram rendering"""
        renderer = MermaidInkRenderer()
        
        with patch("requests.head") as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://mermaid.ink/img/encoded_seq"
            mock_head.return_value = mock_response
            
            result = renderer.render_sequence("sequenceDiagram\n  A->>B: Hello")
            
            assert "mermaid.ink" in result
            mock_head.assert_called_once()
    
    def test_render_exception_handling(self) -> None:
        """Test rendering handles exceptions gracefully"""
        renderer = MermaidInkRenderer()
        
        with patch("requests.head", side_effect=Exception("Network error")):
            result = renderer.render_erd("erDiagram\n  A ||--|| B")
            
            assert "mermaid.ink" in result
    
    def test_custom_base_url(self) -> None:
        """Test custom base URL"""
        renderer = MermaidInkRenderer(base_url="https://custom.mermaid.com/img")
        
        with patch("requests.head") as mock_head:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.url = "https://custom.mermaid.com/img/encoded"
            mock_head.return_value = mock_response
            
            result = renderer.render_erd("graph TD; A-->B;")
            
            assert "custom.mermaid.com" in result
