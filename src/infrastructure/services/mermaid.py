"""Infrastructure - Mermaid Renderer Service Implementation"""

import logging
from urllib.parse import quote

import requests

from src.domain.interfaces.repositories import DiagramRenderer

logger = logging.getLogger(__name__)

MERMAID_INK_URL = "https://mermaid.ink/img"


class MermaidInkRenderer(DiagramRenderer):
    """Mermaid.ink implementation of DiagramRenderer"""
    
    def __init__(self, base_url: str = MERMAID_INK_URL) -> None:
        self._base_url = base_url
    
    def render_erd(self, mermaid_code: str) -> str:
        return self._render(mermaid_code, "erd")
    
    def render_sequence(self, mermaid_code: str) -> str:
        return self._render(mermaid_code, "sequence")
    
    def _render(self, mermaid_code: str, diagram_type: str) -> str:
        try:
            encoded = self._encode(mermaid_code)
            url = f"{self._base_url}/{encoded}"
            
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                logger.info(f"Mermaid {diagram_type} rendered successfully")
                return response.url
            
            logger.warning(f"Mermaid rendering failed: {response.status_code}")
            return url
            
        except Exception as e:
            logger.error(f"Mermaid rendering error: {e}")
            return f"{self._base_url}/{self._encode(mermaid_code)}"
    
    @staticmethod
    def _encode(code: str) -> str:
        return quote(code.strip(), safe="")
