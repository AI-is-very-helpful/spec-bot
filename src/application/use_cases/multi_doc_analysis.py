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


# Document file names
DOCUMENT_FILES = [
    "api_spec.md",
    "erd.md",
    "sequence.md",
    "architecture.md",
    "dependencies.md",
    "structure.md",
    "state_machine.md",
]


@dataclass
class MultiDocumentAnalysisUseCase:
    """Use case for analyzing repository and generating 7 documents"""
    
    github_repository: GitHubRepository
    ai_analyzer: AIAnalyzer
    zip_packager: Any  # ZIPPackagingService
    blob_storage: Any  # AzureBlobStorageService
    card_builder: CardBuilder
    
    def execute(self, input_dto: MultiDocumentAnalysisInput) -> MultiDocumentAnalysisOutput:
        """Execute multi-document analysis
        
        Steps:
        1. Fetch repository data
        2. Generate 7 documents via AI
        3. Package documents into ZIP
        4. Upload to Blob Storage
        5. Generate SAS URL
        """
        
        # Step 1: Parse and validate URL
        logger.info(f"Starting multi-document analysis: {input_dto.github_url}")
        github_url = GitHubURL(value=input_dto.github_url)
        
        # Step 2: Fetch repository metadata
        metadata = self.github_repository.fetch_metadata(github_url)
        
        # Step 3: Fetch file tree
        file_tree = self.github_repository.fetch_file_tree(github_url)
        
        # Step 4: Fetch key source files
        source_files = self.github_repository.fetch_source_files(github_url)
        
        # Step 5: Build repository analysis entity
        analysis = RepositoryAnalysis(
            url=github_url,
            metadata=metadata,
            source_files=source_files,
            file_tree=file_tree,
        )
        
        # Step 6: AI analysis (generates 7 documents)
        # For now, use the multi-doc analyzer interface
        if hasattr(self.ai_analyzer, 'analyze_multidoc'):
            doc_data = self.ai_analyzer.analyze_multidoc(analysis)
        else:
            # Fallback: use existing analyze method and transform
            result_json = self.ai_analyzer.analyze(analysis)
            import json
            doc_data = json.loads(result_json)
            # Transform to new format
            doc_data = {
                "project_summary": doc_data.get("project_summary", {}),
                "api_spec": doc_data.get("api_spec", ""),
                "erd": f"# ERD\n\n{doc_data.get('erd_code', '')}",
                "sequence": f"# Sequence\n\n{doc_data.get('sequence_code', '')}",
                "architecture": "# Architecture\n\n(TBD)",
                "dependencies": "# Dependencies\n\n(TBD)",
                "structure": "# Structure\n\n(TBD)",
                "state_machine": "# State Machine\n\n(TBD)",
            }
        
        # Step 7: Create document dictionary
        documents = {
            "api_spec.md": doc_data.get("api_spec", ""),
            "erd.md": doc_data.get("erd", ""),
            "sequence.md": doc_data.get("sequence", ""),
            "architecture.md": doc_data.get("architecture", ""),
            "dependencies.md": doc_data.get("dependencies", ""),
            "structure.md": doc_data.get("structure", ""),
            "state_machine.md": doc_data.get("state_machine", ""),
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
            document_count=7,
            expires_in_seconds=upload_result.expires_in_seconds,
        )
