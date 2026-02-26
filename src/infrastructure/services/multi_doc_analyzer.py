"""Infrastructure - Multi-Document Azure OpenAI Service"""

import json
import logging
from typing import Any

from openai import AzureOpenAI

from src.domain.entities.repository import RepositoryAnalysis
from src.domain.interfaces.repositories import AIAnalyzer

logger = logging.getLogger(__name__)

MULTI_DOC_SYSTEM_PROMPT = """You are an expert software architect AI. Your task is to analyze source code and generate 7 comprehensive technical documents.

## Your Role
Analyze code to understand project structure, architecture, and patterns, then generate:
1. API Specification (OpenAPI 3.0 style)
2. ERD (Entity Relationship Diagram with Mermaid erDiagram)
3. Sequence Diagram (Business logic flows with Mermaid sequenceDiagram)
4. Architecture Diagram (Layer/Module structure with Mermaid flowchart)
5. Setup & Dependencies (Build tools, external services, libraries)
6. Project Structure (Directory tree with AI annotations)
7. State Machine Diagram (Domain lifecycle with Mermaid stateDiagram)

## Mermaid Syntax Rules (STRICT)
- ALWAYS use proper Mermaid syntax
- ERD: Use 'erDiagram' keyword
- Sequence: Use 'sequenceDiagram' keyword
- Architecture: Use 'flowchart' or 'graph' keyword
- State: Use 'stateDiagram-v2' keyword
- DO NOT wrap mermaid code in markdown code blocks

## Output Format
Return ONLY a JSON object (no additional text):
{
  "project_summary": {
    "name": "Project Name",
    "purpose": "What this project does",
    "tech_stack": ["Tech1", "Tech2"],
    "architecture": "e.g., MVC, Microservices, Layered",
    "folder_structure": ["src/", "tests/", "config/"]
  },
  "api_spec": "# API Specification\\n\\n## Endpoints\\n...",
  "erd": "# ERD\\n\\n```mermaid\\nerDiagram\\n  ...\\n```",
  "sequence": "# Sequence Diagram\\n\\n```mermaid\\nsequenceDiagram\\n  ...\\n```",
  "architecture": "# Architecture\\n\\n```mermaid\\nflowchart\\n  ...\\n```",
  "dependencies": "# Setup & Dependencies\\n\\n## Tech Stack\\n...",
  "structure": "# Project Structure\\n\\n```\\nsrc/\\n  controllers/\\n  ...\\n```\\n\\n## Annotations\\n...",
  "state_machine": "# State Machine\\n\\n```mermaid\\nstateDiagram-v2\\n  ...\\n```"
}

## Guidelines
1. Analyze ALL provided source files
2. Look for: controllers/routes, entities/models, services, config files, enums
3. For architecture: identify layers (presentation, business, data)
4. For dependencies: find pom.xml, requirements.txt, package.json, docker-compose.yml
5. For state machine: find status enums, stateful services
6. Be concise but include all critical information
"""


class MultiDocumentAnalyzer:
    """Azure OpenAI service for generating 7 technical documents"""
    
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
    
    def analyze(self, analysis: RepositoryAnalysis) -> dict[str, Any]:
        """Analyze repository and generate all 7 documents
        
        Args:
            analysis: Repository analysis with source files
            
        Returns:
            Dictionary containing all 7 documents
        """
        logger.info(
            f"Starting multi-document analysis for {analysis.metadata.owner}/"
            f"{analysis.metadata.name}"
        )
        
        context = self._build_context(analysis)
        
        user_prompt = f"""## Repository Information
- URL: {analysis.url.value}
- Language: {analysis.metadata.language or 'Unknown'}
- Description: {analysis.metadata.description or 'N/A'}
- Total files: {len(analysis.source_files)}

## Source Code to Analyze
{context}

Generate all 7 documents following the output format. Include:
1. API endpoints and their parameters/responses
2. Entity relationships for ERD
3. Key service methods for sequence diagram
4. Layer structure for architecture diagram
5. Dependencies from build/config files
6. Directory structure with role annotations
7. Status enums or stateful logic for state machine"""

        try:
            response = self._client.chat.completions.create(
                model=self._deployment_name,
                messages=[
                    {"role": "system", "content": MULTI_DOC_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=12000,
                response_format={"type": "json_object"},
            )
            
            result = response.choices[0].message.content
            logger.info(f"Multi-document response received, length: {len(result)} chars")
            
            # Parse JSON
            result_dict = json.loads(result)
            
            # Validate required keys
            required_keys = [
                "project_summary", "api_spec", "erd", "sequence",
                "architecture", "dependencies", "structure", "state_machine"
            ]
            
            for key in required_keys:
                if key not in result_dict:
                    logger.warning(f"Missing key in response: {key}")
                    result_dict[key] = ""
            
            return result_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            raise ValueError("Failed to parse AI response")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _build_context(self, analysis: RepositoryAnalysis) -> str:
        """Build context from repository analysis"""
        context_parts: list[str] = []
        
        # File tree
        if analysis.file_tree:
            context_parts.append("## File Structure")
            for key, value in analysis.file_tree.items():
                if isinstance(value, dict):
                    context_parts.append(f"- {key}/")
                    for sub in value:
                        context_parts.append(f"  - {sub}")
                else:
                    context_parts.append(f"- {key}")
        
        # Source files
        for source_file in analysis.source_files:
            context_parts.append(
                f"\n### File: {source_file.path} (Type: {source_file.file_type.value})"
            )
            # Truncate long content
            content = source_file.content[:3000]
            context_parts.append(f"\n```\n{content}\n```")
        
        return "\n".join(context_parts)
