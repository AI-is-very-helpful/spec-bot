"""Teams Bot Webhook Handler - Azure Functions HTTP Trigger"""

import json
import logging
import re
from typing import Optional

import azure.functions as func

from app.config import get_settings
from app.services.github import GitHubScraper
from app.services.openai_service import OpenAIService
from app.services.mermaid_renderer import MermaidRenderer
from app.services.adaptive_card import AdaptiveCardBuilder

logger = logging.getLogger(__name__)


# GitHub URL 패턴
GITHUB_URL_PATTERN = r"https?://github\.com/[\w-]+/[\w.-]+/?"
GITHUB_URL_REGEX = re.compile(GITHUB_URL_PATTERN, re.IGNORECASE)


def extract_github_url(message_text: str) -> Optional[str]:
    """메시지에서 GitHub URL 추출"""
    match = GITHUB_URL_REGEX.search(message_text)
    if match:
        url = match.group(0)
        # 끝의 / 제거
        return url.rstrip("/")
    return None


async def analyze_repository(repo_url: str, github_token: Optional[str] = None) -> dict:
    """레포지토리 분석 실행
    
    Returns:
        분석 결과가 포함된 딕셔너리
    """
    # 1. GitHub 스크래핑
    scraper = GitHubScraper(token=github_token)
    repo_analysis = scraper.scrape(repo_url)
    
    # 2. AI 분석
    openai_service = OpenAIService()
    analysis_result = openai_service.analyze_repository(repo_analysis)
    
    # 3. Mermaid 렌더링
    erd_image_url = MermaidRenderer.get_direct_url(analysis_result.erd_code)
    sequence_image_url = MermaidRenderer.get_direct_url(analysis_result.sequence_code)
    
    # 4. Adaptive Card 생성
    card = AdaptiveCardBuilder.build_analysis_card(
        repo_url=repo_url,
        analysis_result=analysis_result,
        erd_image_url=erd_image_url,
        sequence_image_url=sequence_image_url
    )
    
    return {
        "card": card,
        "api_spec": analysis_result.api_spec,
        "summary": analysis_result.project_summary
    }


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Functions HTTP Trigger 엔트리 포인트"""
    logger.info("Spec Bot function triggered")
    
    try:
        req_body = req.get_json()
    except:
        req_body = {}
    
    # Teams 메시지 파싱
    message = None
    if req_body.get("type") == "message":
        message = req_body.get("text", "")
    elif req_body.get("type") == "invoke":
        # Adaptive Card 제출 처리
        return func.HttpResponse(
            json.dumps({"statusCode": 200}),
            mimetype="application/json"
        )
    
    # 도움말 명령어
    if not message or message.lower() in ["help", "/help", "도움말"]:
        return func.HttpResponse(
            json.dumps(AdaptiveCardBuilder.build_help_message()),
            mimetype="application/json",
            status_code=200
        )
    
    # GitHub URL 추출
    repo_url = extract_github_url(message)
    
    if not repo_url:
        return func.HttpResponse(
            json.dumps(AdaptiveCardBuilder.build_error_message(
                "GitHub 레포지토리 URL을 찾을 수 없습니다.\n\n"
                "예: @Spec Bot https://github.com/owner/repo"
            )),
            mimetype="application/json",
            status_code=200
        )
    
    logger.info(f"Processing repository: {repo_url}")
    
    # 설정에서 GitHub 토큰 가져오기
    settings = get_settings()
    github_token = settings.github_token
    
    # ACK 메시지 즉시 반환
    # Note: 실제 구현에서는 Durable Functions를 사용하여
    # 백그라운드에서 처리하고 결과를 별도로 전송
    
    try:
        # 분석 실행 (동기 처리)
        result = await analyze_repository(repo_url, github_token)
        
        # 결과 반환
        return func.HttpResponse(
            json.dumps(result["card"], ensure_ascii=False),
            mimetype="application/json",
            status_code=200
        )
        
    except Exception as e:
        logger.error(f"Error during analysis: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps(AdaptiveCardBuilder.build_error_message(str(e))),
            mimetype="application/json",
            status_code=200
        )
