"""Azure OpenAI Service - 문서 자동 생성"""

import json
import logging
from typing import Optional

from openai import AzureOpenAI

from app.config import get_settings
from app.models.schemas import AnalysisResult
from app.services.github import RepositoryAnalysis

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """You are an expert software architect AI. Your task is to analyze source code and generate comprehensive technical documentation.

## Your Role
- Analyze code to understand project structure, architecture, and patterns
- Generate API specifications in OpenAPI 3.0 style
- Create ERD diagrams using Mermaid syntax
- Create sequence diagrams showing business logic flows
- Provide high-level project summaries

## Mermaid Syntax Rules (STRICT)
- ALWAYS use proper Mermaid syntax
- For ERD: Use 'erDiagram' keyword, define entities with fields, show relationships
- For Sequence: Use 'sequenceDiagram', define participants, show arrows with messages
- DO NOT use markdown code blocks in your mermaid code output
- Use proper Mermaid v10+ syntax

## Output Format
Return a JSON object with this structure:
{
  "project_summary": {
    "name": "Project Name",
    "purpose": "What this project does",
    "tech_stack": ["Tech1", "Tech2"],
    "architecture": "e.g., MVC, Microservices, Layered",
    "folder_structure": ["src/", "tests/", "config/"]
  },
  "api_spec": "Markdown formatted API specification",
  "erd_code": "Mermaid erDiagram code only (no markdown)",
  "sequence_code": "Mermaid sequenceDiagram code only (no markdown)",
  "key_insights": ["Insight 1", "Insight 2"]
}

## Guidelines
- Analyze the provided source files carefully
- Identify REST endpoints, controllers, routes
- Identify database entities/models and their relationships
- Identify service layer business logic for sequence diagrams
- Be concise but comprehensive
"""


class OpenAIService:
    """Azure OpenAI Service for document generation"""
    
    def __init__(self):
        settings = get_settings()
        
        self.client = AzureOpenAI(
            api_key=settings.openai_api_key,
            api_version=settings.openai_api_version,
            azure_endpoint=settings.openai_api_endpoint,
            deployment=settings.openai_deployment_name
        )
        
        self.system_prompt = SYSTEM_PROMPT
    
    def _build_context(self, repo_analysis: RepositoryAnalysis) -> str:
        """소스 코드에서 컨텍스트 구축"""
        context_parts = []
        
        # 파일 트리 정보
        if repo_analysis.file_tree:
            context_parts.append("## File Structure")
            for key, value in repo_analysis.file_tree.items():
                context_parts.append(f"- {key}")
        
        # 파일별 컨텍스트
        for file in repo_analysis.files:
            context_parts.append(f"\n## File: {file.path} (Type: {file.file_type})")
            context_parts.append(f"\n```\n{file.content}\n```")
        
        return "\n".join(context_parts)
    
    def analyze_repository(self, repo_analysis: RepositoryAnalysis) -> AnalysisResult:
        """레포지토리 분석 실행"""
        logger.info(f"Starting AI analysis for {repo_analysis.owner}/{repo_analysis.repo_name}")
        
        context = self._build_context(repo_analysis)
        
        user_prompt = f"""## Repository Information
- URL: {repo_analysis.url}
- Language: {repo_analysis.language or 'Unknown'}
- Description: {repo_analysis.description or 'N/A'}

## Source Code to Analyze
{context}

Please analyze this code and generate the documentation following the output format. Focus on:
1. Extracting API endpoints from controllers/routes
2. Identifying entities/models and their relationships for ERD
3. Finding key service layer methods for sequence diagrams"""

        try:
            response = self.client.chat.completions.create(
                model=get_settings().openai_deployment_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=8000,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            logger.info(f"OpenAI response received, length: {len(result_text)} chars")
            
            # JSON 파싱
            result_dict = json.loads(result_text)
            analysis_result = AnalysisResult(**result_dict)
            
            logger.info("Analysis completed successfully")
            return analysis_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            raise ValueError("Failed to parse AI response")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
