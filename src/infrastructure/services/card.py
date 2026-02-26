"""Infrastructure - Adaptive Card Builder Implementation"""

import logging
from typing import Any

from src.domain.interfaces.repositories import CardBuilder

logger = logging.getLogger(__name__)


class TeamsCardBuilder(CardBuilder):
    """Teams Adaptive Card implementation of CardBuilder"""

    def build_result_card(
        self,
        repo_url: str,
        api_spec: str,
        erd_image_url: str,
        sequence_image_url: str,
        summary: dict[str, Any],
        insights: list[str],
        download_url: str = ""
    ) -> dict:
        card: dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": f"📊 {summary.get('name', 'Project')} - 분석 완료",
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
                {
                    "type": "TextBlock",
                    "text": "📋 프로젝트 요약",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"**목적:** {summary.get('purpose', 'N/A')}",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"**아키텍처:** {summary.get('architecture', 'N/A')}",
                    "wrap": True,
                    "spacing": "None"
                },
                {
                    "type": "TextBlock",
                    "text": f"**기술 스택:** {', '.join(summary.get('tech_stack', []))}",
                    "wrap": True,
                    "spacing": "None"
                },
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
                {
                    "type": "TextBlock",
                    "text": "💡 주요 발견 사항",
                    "weight": "Bolder",
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": "\n".join([f"• {i}" for i in insights[:5]]),
                    "wrap": True,
                    "spacing": "None"
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "📦 기술 문서 패키지 다운로드 (.zip)",
                    "url": download_url if download_url else repo_url
                },
                {
                    "type": "Action.OpenUrl",
                    "title": "GitHub에서 보기",
                    "url": repo_url
                }
            ]
        }

        logger.info("Adaptive Card built successfully")
        return card

    def build_ack_message(self) -> dict:
        return {
            "type": "message",
            "text": (
                "🔍 프로젝트 분석을 시작합니다.\n\n"
                "다수의 문서를 생성하므로 약 1~2분 소요될 수 있습니다."
            )
        }

    def build_error_message(self, error: str) -> dict:
        return {
            "type": "message",
            "text": f"❌ 오류가 발생했습니다.\n\n{error}\n\n다시 시도해 주세요."
        }

    def build_help_message(self) -> dict:
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
- 🔗 ERD 관계 다이어그램 (엔티티)
- 🔄 시퀀스 다이어그램 (비즈니스 플로우)
- 📦 ZIP 파일 (5개 문서 패키지)

**주의:** Public 레포지토리만 지원됩니다.
"""
        }

    def build_download_card(
        self,
        summary: dict[str, str],
        download_url: str,
        document_count: int,
        expires_in_seconds: int,
    ) -> dict:
        """Build adaptive card with download button for ZIP file"""
        import math

        # Calculate expiry time in hours
        expiry_hours = math.ceil(expires_in_seconds / 3600)

        card: dict[str, Any] = {
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "📊 분석 완료!",
                    "weight": "Bolder",
                    "size": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"**{summary.get('name', 'Project')}**",
                    "weight": "Bolder",
                    "wrap": True
                },
                {
                    "type": "TextBlock",
                    "text": f"**목적:** {summary.get('purpose', 'N/A')}",
                    "wrap": True,
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"**아키텍처:** {summary.get('architecture', 'N/A')}",
                    "wrap": True,
                    "spacing": "None"
                },
                {
                    "type": "TextBlock",
                    "text": f"**기술 스택:** {', '.join(summary.get('tech_stack', []))}",
                    "wrap": True,
                    "spacing": "None"
                },
                {
                    "type": "TextBlock",
                    "text": f"📄 **생성된 문서:** {document_count}개",
                    "wrap": True,
                    "spacing": "Medium"
                },
                {
                    "type": "TextBlock",
                    "text": f"⏰ **다운로드 링크 유효 기간:** {expiry_hours}시간",
                    "wrap": True,
                    "isSubtle": True,
                    "spacing": "None"
                }
            ],
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "📦 기술 문서 패키지 다운로드 (.zip)",
                    "url": download_url
                }
            ]
        }

        logger.info("Download card built successfully")
        return card
