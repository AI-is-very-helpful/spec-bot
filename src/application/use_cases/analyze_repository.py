"""Application layer - Use Cases"""

import logging
from dataclasses import dataclass

from src.application.dto.repository import (
    AnalyzeRepositoryInput,
    AnalyzeRepositoryOutput,
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


@dataclass
class AnalyzeRepositoryUseCase:
    """Analyze GitHub repository and generate documentation"""
    
    github_repository: GitHubRepository
    ai_analyzer: AIAnalyzer
    diagram_renderer: DiagramRenderer
    card_builder: CardBuilder
    
    def execute(self, input_dto: AnalyzeRepositoryInput) -> AnalyzeRepositoryOutput:
        """Execute repository analysis"""
        
        # Step 1: Parse and validate URL
        logger.info(f"Analyzing repository: {input_dto.github_url}")
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
        
        # Step 6: AI analysis
        ai_result_json = self.ai_analyzer.analyze(analysis)
        
        # Step 7: Parse AI result
        from src.domain.entities.repository import AnalysisResult
        import json
        result_dict = json.loads(ai_result_json)
        analysis_result = AnalysisResult(
            project_summary=result_dict["project_summary"],
            api_spec=result_dict["api_spec"],
            erd_code=result_dict["erd_code"],
            sequence_code=result_dict["sequence_code"],
            key_insights=tuple(result_dict["key_insights"]),
        )
        
        # Step 8: Render diagrams
        erd_image_url = self.diagram_renderer.render_erd(result_dict["erd_code"])
        sequence_image_url = self.diagram_renderer.render_sequence(
            result_dict["sequence_code"]
        )
        
        # Step 9: Build adaptive card
        card = self.card_builder.build_result_card(
            repo_url=input_dto.github_url,
            api_spec=result_dict["api_spec"],
            erd_image_url=erd_image_url,
            sequence_image_url=sequence_image_url,
            summary=result_dict["project_summary"],
            insights=result_dict["key_insights"],
        )
        
        return AnalyzeRepositoryOutput(
            card=card,
            api_spec=result_dict["api_spec"],
            erd_image_url=erd_image_url,
            sequence_image_url=sequence_image_url,
            summary=result_dict["project_summary"],
            insights=result_dict["key_insights"],
        )
