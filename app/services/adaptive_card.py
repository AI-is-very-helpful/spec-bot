"""Adaptive Card Builder - Teams에 전송할 Adaptive Card 생성"""

import json
import logging
from dataclasses import dataclass

from app.models.schemas import AnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class CardImage:
    """카드에 포함될 이미지 정보"""
    url: str
    alt: str


class AdaptiveCardBuilder:
    """Teams Adaptive Card 빌더"""
    
    @staticmethod
    def build_analysis_card(
        repo_url: str,
        analysis_result: AnalysisResult,
        erd_image_url: str,
        sequence_image_url: str
    ) -> dict:
        """분석 결과 Adaptive Card 생성
        
        Args:
            repo_url: GitHub 레포지토리 URL
            analysis_result: AI 분석 결과
            erd_image_url: ERD 이미지 URL
            sequence_image_url: 시퀀스 다이어그램 이미지 URL
            
        Returns:
            Adaptive Card JSON
        """
        summary = analysis_result.project_summary
        
        card = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                # 헤더
                {
                    "type": "TextBlock",
                    "text": f"📊 {summary.name} - 분석 완료",
                    "weight": "Bolder",
                    "size": "Medium",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"[GitHub에서 보기]({repo_url})",
                    "isSubtle": True,
                    "wrap": True,
                    "spacing": "None"
                },
                
                # 프로젝트 요약
                {
                    "type": "TextBlock",
                    "text": "📋 프로젝트 요약",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"**목적:** {summary.purpose}",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"**아키텍처:** {summary.architecture}",
                    "wrap": True,
                    "spacing": "None"
                },
                {
                    "type": "TextBlock",
                    "text": f"**기술 스택:** {', '.join(summary.tech_stack)}",
                    "wrap": True,
                    "spacing": "None"
                },
                
                # ERD 다이어그램
                {
                    "type": "TextBlock",
                    "text": "🔗 ERD (Entity Relationship)",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "Image",
                    "url": erd_image_url,
                    "altText": "ERD Diagram",
                    "size": "Stretch",
                    "spacing": "None"
                },
                
                # 시퀀스 다이어그램
                {
                    "type": "TextBlock",
                    "text": "🔄 시퀀스 다이어그램",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "Image",
                    "url": sequence_image_url,
                    "altText": "Sequence Diagram",
                    "size": "Stretch",
                    "spacing": "None"
                },
                
                # 주요 발견 사항
                {
                    "type": "TextBlock",
                    "text": "💡 주요 발견 사항",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": "\n".join([f"• {insight}" for insight in analysis_result.key_insights[:5]]),
                    "wrap": True,
                    "spacing": "None"
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "GitHub에서 보기",
                    "url": repo_url
                }
            ]
        }
        
        logger.info("Adaptive Card built successfully")
        return card
    
    @staticmethod
    def build_ack_message() -> str:
        """분석 시작 ACK 메시지"""
        return {
            "type": "message",
            "text": "🔍 분석을 시작합니다.\n\nGitHub 레포지토리를 분석하여 API Spec, ERD, 시퀀스 다이어그램을 생성합니다.\n\n(최대 30~60초 소요)"
        }
    
    @staticmethod
    def build_error_message(error: str) -> str:
        """오류 메시지"""
        return {
            "type": "message",
            "text": f"❌ 오류가 발생했습니다.\n\n{error}\n\n다시 시도해 주세요."
        }
    
    @staticmethod
    def build_help_message() -> str:
        """도움말 메시지"""
        return {
            "type": "message",
            "text": """📖 **Spec Bot 사용법**

GitHub 레포지토리 URL을 입력하면 AI가 자동으로 기술 문서를 생성합니다.

**사용 예시:**
```
@Spec Bot https://github.com/owner/repo
```

**생성되는 문서:**
- 📋 프로젝트 요약 (목적, 기술 스택, 아키텍처)
- 🔗 ERD (엔티티 관계 다이어그램)
- 🔄 시퀀스 다이어그램 (비즈니스 플로우)

**주의:** Public 레포지토리만 지원됩니다.
"""
        }
