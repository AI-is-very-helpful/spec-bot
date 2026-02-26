"""Infrastructure - Azure OpenAI Service Implementation"""

import json
import logging
from typing import Optional

from openai import AzureOpenAI

from src.domain.entities.repository import RepositoryAnalysis
from src.domain.interfaces.repositories import AIAnalyzer

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


class AzureOpenAIService(AIAnalyzer):
    """Azure OpenAI implementation of AIAnalyzer"""
    
    def __init__(
        self,
        api_key: str,
        api_endpoint: str,
        api_version: str,
        deployment_name: str,
    ) -> None:
        self._client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=api_endpoint,
            azure_deployment=deployment_name,
        )
        self._deployment_name = deployment_name
    
    def analyze(self, analysis: RepositoryAnalysis) -> str:
        logger.info(
            f"Starting AI analysis for {analysis.metadata.owner}/"
            f"{analysis.metadata.name}"
        )
        
        context = self._build_context(analysis)
        
        user_prompt = f"""## Repository Information
- URL: {analysis.url.value}
- Language: {analysis.metadata.language or 'Unknown'}
- Description: {analysis.metadata.description or 'N/A'}

## Source Code to Analyze
{context}

Please analyze this code and generate the documentation following the output format. Focus on:
1. Extracting API endpoints from controllers/routes
2. Identifying entities/models and their relationships for ERD
3. Finding key service layer methods for sequence diagrams"""
        
        try:
            response = self._client.chat.completions.create(
                model=self._deployment_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=8000,
                response_format={"type": "json_object"},
            )
            
            result = response.choices[0].message.content
            logger.info(f"OpenAI response received, length: {len(result)} chars")
            
            # Validate JSON
            json.loads(result)
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            raise ValueError("Failed to parse AI response")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _build_context(self, analysis: RepositoryAnalysis) -> str:
        context_parts: list[str] = []
        
        # File tree
        if analysis.file_tree:
            context_parts.append("## File Structure")
            for key in analysis.file_tree:
                context_parts.append(f"- {key}")
        
        # Source files
        for source_file in analysis.source_files:
            context_parts.append(
                f"\n## File: {source_file.path} "
                f"(Type: {source_file.file_type.value})"
            )
            context_parts.append(f"\n```\n{source_file.content}\n```")
        
        return "\n".join(context_parts)
