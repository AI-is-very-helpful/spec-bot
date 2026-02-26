"""Mermaid Renderer - Mermaid 코드를 이미지로 변환"""

import logging
from urllib.parse import quote

import requests

logger = logging.getLogger(__name__)

MERMAID_INK_URL = "https://mermaid.ink/img"


class MermaidRenderer:
    """Mermaid 코드를 이미지로 변환하는 서비스"""
    
    @staticmethod
    def encode_mermaid(code: str) -> str:
        """Mermaid 코드를 URL-safe 형식으로 인코딩"""
        # 줄바꿈과 공백 처리
        encoded = code.strip()
        encoded = quote(encoded, safe="")
        return encoded
    
    @staticmethod
    def render(mermaid_code: str, diagram_type: str = "general") -> str:
        """Mermaid 코드를 이미지로 변환
        
        Args:
            mermaid_code: Mermaid 다이어그램 코드
            diagram_type: 다이어그램 타입 (erd, sequence, etc.)
            
        Returns:
            이미지를 포함한 마크다운 문자열
        """
        try:
            encoded = MermaidRenderer.encode_mermaid(mermaid_code)
            
            # Mermaid.ink URL 생성
            url = f"{MERMAID_INK_URL}/{encoded}"
            
            # URL 접근 가능 확인
            response = requests.head(url, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                image_url = response.url
                logger.info(f"Mermaid {diagram_type} rendered successfully")
                
                # 마크다운 이미지 형식으로 반환
                return f"![{diagram_type}]({image_url})"
            else:
                logger.warning(f"Mermaid rendering failed: {response.status_code}")
                # 실패 시 코드 자체를 반환
                return f"```{mermaid_code}\n```"
                
        except Exception as e:
            logger.error(f"Mermaid rendering error: {e}")
            return f"```mermaid\n{mermaid_code}\n```"
    
    @staticmethod
    def get_direct_url(mermaid_code: str) -> str:
        """Mermaid 코드에서 직접 이미지 URL 반환"""
        encoded = MermaidRenderer.encode_mermaid(mermaid_code)
        return f"{MERMAID_INK_URL}/{encoded}"
