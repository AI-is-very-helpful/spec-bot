"""Unit tests for Use Cases - AnalyzeRepositoryUseCase"""

import json
import pytest
from unittest.mock import Mock, MagicMock

from src.application.dto.repository import AnalyzeRepositoryInput
from src.application.use_cases.analyze_repository import AnalyzeRepositoryUseCase
from src.domain.entities.repository import (
    FileType,
    RepositoryAnalysis,
    RepositoryMetadata,
    SourceFile,
)
from src.domain.value_objects import GitHubURL


class TestAnalyzeRepositoryUseCase:
    """Test cases for AnalyzeRepositoryUseCase"""
    
    def _create_mock_dependencies(self) -> tuple:
        """Create mock dependencies"""
        github_repo = Mock()
        ai_analyzer = Mock()
        diagram_renderer = Mock()
        card_builder = Mock()
        
        return github_repo, ai_analyzer, diagram_renderer, card_builder
    
    def _create_sample_analysis(self) -> RepositoryAnalysis:
        """Create sample repository analysis"""
        url = GitHubURL(value="https://github.com/owner/repo")
        meta = RepositoryMetadata(
            owner="owner",
            name="repo",
            url=url.value,
            language="Python",
            description="A test repository"
        )
        
        files = [
            SourceFile(
                path="src/controllers/user.py",
                content="def get_user(): pass",
                file_type=FileType.CONTROLLER
            ),
            SourceFile(
                path="src/services/user.py",
                content="class UserService: pass",
                file_type=FileType.SERVICE
            ),
            SourceFile(
                path="src/models/user.py",
                content="class User: pass",
                file_type=FileType.ENTITY
            ),
        ]
        
        return RepositoryAnalysis(
            url=url,
            metadata=meta,
            source_files=files,
            file_tree={"src": {"controllers": "src/controllers"}}
        )
    
    def test_execute_success(self) -> None:
        """Test successful execution"""
        # Setup mocks
        github_repo, ai_analyzer, diagram_renderer, card_builder = \
            self._create_mock_dependencies()
        
        analysis = self._create_sample_analysis()
        github_repo.fetch_metadata.return_value = analysis.metadata
        github_repo.fetch_file_tree.return_value = analysis.file_tree
        github_repo.fetch_source_files.return_value = analysis.source_files
        
        ai_result = {
            "project_summary": {
                "name": "TestRepo",
                "purpose": "A test project",
                "tech_stack": ["Python", "FastAPI"],
                "architecture": "MVC",
                "folder_structure": ["src/", "tests/"]
            },
            "api_spec": "# API Spec",
            "erd_code": "erDiagram\n  A ||--|| B",
            "sequence_code": "sequenceDiagram\n  A->>B: Hello",
            "key_insights": ["Insight 1"]
        }
        ai_analyzer.analyze.return_value = json.dumps(ai_result)
        
        # Setup return values
        diagram_renderer.render_erd.return_value = "https://mermaid.ink/img/erd"
        diagram_renderer.render_sequence.return_value = "https://mermaid.ink/img/seq"
        card_builder.build_result_card.return_value = {"type": "AdaptiveCard"}
        
        # Execute
        use_case = AnalyzeRepositoryUseCase(
            github_repository=github_repo,
            ai_analyzer=ai_analyzer,
            diagram_renderer=diagram_renderer,
            card_builder=card_builder
        )
        
        input_dto = AnalyzeRepositoryInput(github_url="https://github.com/owner/repo")
        result = use_case.execute(input_dto)
        
        # Verify
        assert result.api_spec == "# API Spec"
        assert result.erd_image_url == "https://mermaid.ink/img/erd"
        assert result.sequence_image_url == "https://mermaid.ink/img/seq"
        
        github_repo.fetch_metadata.assert_called_once()
        ai_analyzer.analyze.assert_called_once()
        diagram_renderer.render_erd.assert_called_once()
        diagram_renderer.render_sequence.assert_called_once()
        card_builder.build_result_card.assert_called_once()
    
    def test_execute_parses_github_url(self) -> None:
        """Test that GitHub URL is parsed correctly"""
        github_repo, ai_analyzer, diagram_renderer, card_builder = \
            self._create_mock_dependencies()
        
        # Setup mock for analysis
        url = GitHubURL(value="https://github.com/owner/repo")
        github_repo.fetch_metadata.return_value = RepositoryMetadata(
            owner="owner", name="repo", url=url.value
        )
        github_repo.fetch_file_tree.return_value = {}
        github_repo.fetch_source_files.return_value = []
        
        ai_result = {
            "project_summary": {"name": "R", "purpose": "P", "tech_stack": [],
                              "architecture": "A", "folder_structure": []},
            "api_spec": "", "erd_code": "", "sequence_code": "", "key_insights": []
        }
        ai_analyzer.analyze.return_value = json.dumps(ai_result)
        
        # Setup return values
        diagram_renderer.render_erd.return_value = "https://mermaid.ink/img/erd"
        diagram_renderer.render_sequence.return_value = "https://mermaid.ink/img/seq"
        card_builder.build_result_card.return_value = {"type": "AdaptiveCard"}
        
        use_case = AnalyzeRepositoryUseCase(
            github_repository=github_repo,
            ai_analyzer=ai_analyzer,
            diagram_renderer=diagram_renderer,
            card_builder=card_builder
        )
        
        input_dto = AnalyzeRepositoryInput(github_url="https://github.com/owner/repo")
        use_case.execute(input_dto)
        
        # Verify URL was used
        github_repo.fetch_metadata.assert_called_once()
        call_args = github_repo.fetch_metadata.call_args[0][0]
        assert call_args.value == "https://github.com/owner/repo"
