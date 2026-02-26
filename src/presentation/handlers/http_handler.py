"""Presentation layer - HTTP Handler"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
from dotenv import load_dotenv

# Load .env file if it exists
_env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(_env_path)
from typing import Optional

import azure.functions as func
from pydantic import ValidationError

from src.application.dto.multidoc import MultiDocumentAnalysisInput
from src.application.use_cases.multi_doc_analysis import MultiDocumentAnalysisUseCase
from src.domain.interfaces.repositories import (
    AIAnalyzer,
    CardBuilder,
    DiagramRenderer,
    GitHubRepository,
)
from src.infrastructure.services.blob_storage import AzureBlobStorageService
from src.infrastructure.services.card import TeamsCardBuilder
from src.infrastructure.services.logging_config import get_logger
from src.infrastructure.services.mermaid import MermaidInkRenderer
from src.infrastructure.services.multi_doc_analyzer import MultiDocumentAnalyzer
from src.infrastructure.services.openai import AzureOpenAIService
from src.infrastructure.services.teams_bot import TeamsBotService, MessageFactory
from src.infrastructure.services.zip_packager import ZIPPackagingService

# Configure logger
logger = get_logger("spec_bot.http_handler")


def get_github_repository() -> GitHubRepository:
    """Get GitHub repository instance"""
    # Lazy import to avoid hard dependency
    from src.infrastructure.repositories.github import PyGitHubRepository

    token = os.getenv("GITHUB_TOKEN")
    return PyGitHubRepository(token=token)


def get_ai_analyzer() -> AIAnalyzer:
    """Get AI analyzer instance (MultiDocumentAnalyzer for 7 documents)"""
    return MultiDocumentAnalyzer(
        api_key=os.getenv("OPENAI_API_KEY", ""),
        api_endpoint=os.getenv("OPENAI_API_ENDPOINT", ""),
        api_version=os.getenv("OPENAI_API_VERSION", "2024-02-15-preview"),
        deployment_name=os.getenv("OPENAI_DEPLOYMENT_NAME", "kimi-k2.5"),
    )


def get_zip_packager() -> ZIPPackagingService:
    """Get ZIP packager instance"""
    return ZIPPackagingService()


def get_blob_storage() -> AzureBlobStorageService:
    """Get Blob Storage service instance"""
    return AzureBlobStorageService(
        connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING", ""),
    )


def get_card_builder() -> CardBuilder:
    """Get card builder instance"""
    return TeamsCardBuilder()


def get_teams_bot_service() -> TeamsBotService:
    """Get Teams bot service instance"""
    return TeamsBotService(
        app_id=os.getenv("AZURE_BOT_ID", ""),
        app_password=os.getenv("AZURE_BOT_PASSWORD", ""),
    )


async def main(req: func.HttpRequest) -> func.HttpResponse:
    """Azure Functions HTTP Trigger entry point

    This handler processes incoming requests from Azure Bot Service,
    which forwards Teams messages to this endpoint.
    """
    logger.info("Spec Bot function triggered", extra={"method": req.method})

    try:
        req_body = req.get_json()
    except Exception:
        req_body = {}

    # Get Teams bot service
    bot_service = get_teams_bot_service()

    # Parse Teams activity
    activity = bot_service.parse_teams_activity(req_body)

    if activity is None:
        # Not a valid Teams message
        return func.HttpResponse(
            json.dumps({"status": "OK"}),
            mimetype="application/json",
            status_code=200,
        )

    message = activity.get("text", "")

    # Help command
    if bot_service.is_help_command(message):
        logger.info("Help command received")
        return func.HttpResponse(
            json.dumps(MessageFactory.create_help_message()),
            mimetype="application/json",
            status_code=200,
        )

    # Extract GitHub URL
    repo_url = bot_service.extract_github_url(message)

    if not repo_url:
        logger.info("No GitHub URL found in message", extra={"message": message[:100]})
        return func.HttpResponse(
            json.dumps(MessageFactory.create_github_not_found_message()),
            mimetype="application/json",
            status_code=200,
        )

    logger.info(
        "Processing repository",
        extra={"repo_url": repo_url, "user": activity.get("from", "")},
    )

    # Validate input
    try:
        input_dto = MultiDocumentAnalysisInput(github_url=repo_url)
    except ValidationError as e:
        logger.warning("Input validation failed", extra={"error": str(e)})
        return func.HttpResponse(
            json.dumps(MessageFactory.create_error_message(str(e))),
            mimetype="application/json",
            status_code=200,
        )

    # Send ACK message
    ack_message = MessageFactory.create_ack_message()
    logger.info("ACK message created", extra={"repo_url": repo_url})

    # Execute multi-document analysis use case
    try:
        use_case = MultiDocumentAnalysisUseCase(
            github_repository=get_github_repository(),
            ai_analyzer=get_ai_analyzer(),
            zip_packager=get_zip_packager(),
            blob_storage=get_blob_storage(),
            card_builder=get_card_builder(),
        )

        logger.info("Executing multi-document analysis use case")
        result = use_case.execute(input_dto)

        logger.info(
            "Analysis completed",
            extra={
                "repo_url": repo_url,
                "document_count": result.document_count,
                "zip_url": result.zip_blob_url[:50] + "..." if len(result.zip_blob_url) > 50 else result.zip_blob_url,
            }
        )

        # Build Adaptive Card with download button
        card = get_card_builder().build_download_card(
            summary=result.summary,
            download_url=result.zip_blob_url,
            document_count=result.document_count,
            expires_in_seconds=result.expires_in_seconds,
        )

        return func.HttpResponse(
            json.dumps(card, ensure_ascii=False),
            mimetype="application/json",
            status_code=200,
        )

    except Exception as e:
        logger.error(
            "Analysis failed",
            extra={"repo_url": repo_url, "error": str(e)},
            exc_info=True,
        )
        return func.HttpResponse(
            json.dumps(MessageFactory.create_error_message(str(e))),
            mimetype="application/json",
            status_code=200,
        )
