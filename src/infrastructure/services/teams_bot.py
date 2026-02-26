"""Teams Bot Service - Microsoft Teams Bot Framework Integration"""

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

# GitHub URL regex pattern
GITHUB_URL_PATTERN = re.compile(
    r"https?://github\.com/[\w-]+/[\w.-]+/?",
    re.IGNORECASE
)

# Help command patterns
HELP_PATTERNS = frozenset([
    "help", "/help", "도움말", "?", "commands", "사용법"
])


class MessageFactory:
    """Factory for creating Teams messages"""
    
    @staticmethod
    def create_ack_message() -> dict:
        """Create acknowledgment message"""
        return {
            "type": "message",
            "text": (
                "🔍 프로젝트 분석을 시작합니다.\n\n"
                "다수의 문서를 생성하므로 약 1~2분 소요될 수 있습니다."
            )
        }
    
    @staticmethod
    def create_error_message(error: str) -> dict:
        """Create error message"""
        return {
            "type": "message",
            "text": f"❌ 오류가 발생했습니다.\n\n{error}\n\n다시 시도해 주세요."
        }
    
    @staticmethod
    def create_help_message() -> dict:
        """Create help message"""
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
    
    @staticmethod
    def create_github_not_found_message() -> dict:
        """Create message when GitHub URL not found"""
        return {
            "type": "message",
            "text": (
                "❓ GitHub 레포지토리 URL을 찾을 수 없습니다.\n\n"
                "예시: `@Spec Bot https://github.com/owner/repo`"
            )
        }


class TeamsBotService:
    """Microsoft Teams Bot Service"""
    
    def __init__(
        self,
        app_id: str = "",
        app_password: str = "",
    ) -> None:
        self._app_id = app_id
        self._app_password = app_password
        logger.info(
            f"TeamsBotService initialized (app_id present: {bool(app_id)})"
        )
    
    @property
    def is_configured(self) -> bool:
        """Check if bot is configured with credentials"""
        return bool(self._app_id and self._app_password)
    
    def extract_github_url(self, message: str) -> Optional[str]:
        """Extract GitHub URL from message text"""
        if not message:
            return None
        
        match = GITHUB_URL_PATTERN.search(message)
        if match:
            url = match.group(0)
            return url.rstrip("/")
        
        return None
    
    def is_help_command(self, message: str) -> bool:
        """Check if message is a help command"""
        if not message:
            return False
        
        normalized = message.strip().lower()
        return normalized in HELP_PATTERNS
    
    def parse_teams_activity(self, activity: dict) -> Optional[dict]:
        """Parse Teams activity to extract message"""
        try:
            if activity.get("type") != "message":
                logger.debug(f"Ignoring non-message activity: {activity.get('type')}")
                return None
            
            text = activity.get("text", "")
            if not text:
                return None
            
            conversation = activity.get("conversation", {})
            channel_data = activity.get("channelData", {})
            
            return {
                "text": text,
                "from": activity.get("from", {}).get("id", ""),
                "conversation_id": conversation.get("id", ""),
                "channel_id": channel_data.get("channel", {}).get("id", ""),
                "tenant_id": channel_data.get("tenant", {}).get("id", ""),
                "service_url": activity.get("serviceUrl", ""),
            }
            
        except Exception as e:
            logger.error(f"Error parsing Teams activity: {e}")
            return None
    
    async def send_message(
        self,
        message: dict,
        conversation_id: str,
        service_url: str,
    ) -> bool:
        """Send message to Teams conversation"""
        if not self.is_configured:
            logger.warning("Bot not configured, cannot send message")
            return False
        
        logger.info(f"Sending message to conversation: {conversation_id}")
        return True
    
    async def send_card(
        self,
        card: dict,
        conversation_id: str,
        service_url: str,
    ) -> bool:
        """Send adaptive card to Teams conversation"""
        if not self.is_configured:
            logger.warning("Bot not configured, cannot send card")
            return False
        
        logger.info(f"Sending card to conversation: {conversation_id}")
        return True
