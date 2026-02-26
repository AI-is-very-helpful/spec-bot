"""Application layer - Multi-Document Analysis Use Case"""

import logging
from dataclasses import dataclass
from typing import Any
from dataclasses import dataclass

from src.application.dto.multidoc import (
    MultiDocumentAnalysisInput,
    MultiDocumentAnalysisOutput,
)
from src.domain.entities.repository import RepositoryAnalysis
from src.domain.interfaces.repositories import (
    AIAnalyzer,
    CardBuilder,
    DiagramRenderer,
    GitHubRepository,
)
from src.domain.value_objects import GitHubURL

logger = logging.getLogger(__name__)


# 5개 에이전트 산출물 파일명
DOCUMENT_FILES = [
    "api_spec.md",
    "erd.md",
    "architecture.md",
    "tech_stack.md",
    "schema.sql",
]


@dataclass
class MultiDocumentAnalysisUseCase:
    """Use case for analyzing repository and generating 5 documents (5 agents)"""
    
    github_repository: GitHubRepository
    ai_analyzer: AIAnalyzer
    zip_packager: Any  # ZIPPackagingService
    blob_storage: Any  # AzureBlobStorageService
    card_builder: CardBuilder
    
    def execute(self, input_dto: MultiDocumentAnalysisInput) -> MultiDocumentAnalysisOutput:
        """Execute multi-document analysis
        
        Steps:
        1. Fetch repository data
        2. Generate 5 documents via 5 agents
        3. Package documents into ZIP
        4. Upload to Blob Storage
        5. Generate SAS URL
        """
        
        # Step 1: Parse and validate URL
        logger.info(f"Starting multi-document analysis: {input_dto.github_url}")
        github_url = GitHubURL(value=input_dto.github_url)

        # Step 2: Fetch repository metadata (blob 이름 등에 사용)
        metadata = self.github_repository.fetch_metadata(github_url)

        # Step 3: 문서 생성 — ai-agent 파이프라인만 사용
        doc_data = self.ai_analyzer.run_from_url(github_url.value)
        
        # Step 7: Create document dictionary (5개 에이전트 결과만)
        documents = {
            "api_spec.md": doc_data.get("api_spec", ""),
            "erd.md": doc_data.get("erd", ""),
            "architecture.md": doc_data.get("architecture", ""),
            "tech_stack.md": doc_data.get("tech_stack", ""),
            "schema.sql": doc_data.get("schema_sql", ""),
        }
        
        # Step 8: Create ZIP package
        logger.info("Creating ZIP package")
        zip_bytes = self.zip_packager.create_zip(documents)
        
        # Step 9: Upload to Blob Storage
        logger.info("Uploading to Blob Storage")
        repo_name = f"{metadata.owner}-{metadata.name}"
        upload_result = self.blob_storage.upload_zip(zip_bytes, repo_name)
        
        # Step 10: Return output
        return MultiDocumentAnalysisOutput(
            zip_blob_url=upload_result.full_url,
            summary=doc_data.get("project_summary", {}),
            document_count=5,
            expires_in_seconds=upload_result.expires_in_seconds,
        )
