"""Infrastructure - Parallel Document Generator (asyncio-based)"""

import asyncio
import json
import logging
from typing import Any, Optional

from openai import AzureOpenAI

logger = logging.getLogger(__name__)

# System prompts for each document type
SYSTEM_PROMPTS: dict[str, str] = {
    "api_spec": """You are an expert API documentation generator. Generate an OpenAPI 3.0 style API specification.

## Requirements (CRITICAL - MUST INCLUDE ALL):
1. **Request Body**: For POST/PUT endpoints, include complete schema with all fields, types, required/optional, examples
2. **Response Body**: Include status codes (200, 201, 400, 401, 404, 500) with response schemas and examples
3. **Headers**: Include authentication headers (Authorization, Content-Type), custom headers
4. **Path Parameters**: Include type, description, example values
5. **Query Parameters**: Include type, required/optional, description, default values

## Output Format:
Return JSON with:
{
  "content": "# API Specification\\n\\n## Endpoints\\n..."
}

Use proper OpenAPI 3.0 terminology and include realistic examples.""",

    "erd": """You are an expert database architect. Generate an ERD using Mermaid erDiagram.

## Requirements:
1. Analyze entity classes and their relationships
2. Include proper cardinality (one-to-one, one-to-many, many-to-many)
3. Include primary keys, foreign keys, and important attributes
4. Add relationship descriptions

## Mermaid Syntax:
```mermaid
erDiagram
  USER ||--o{ ORDER : places
  ORDER ||--|{ ORDER_ITEM : contains
```

Return JSON:
{
  "content": "# ERD\\n\\n```mermaid\\nerDiagram\\n...\\n```"
}""",

    "sequence": """You are an expert software architect. Generate a sequence diagram using Mermaid sequenceDiagram.

## Requirements:
1. Identify key service methods and their interactions
2. Show actor/participant interactions with proper arrows
3. Include loop, alt, opt fragments for complex logic
4. Add activation boxes

## Mermaid Syntax:
```mermaid
sequenceDiagram
  participant U as User
  participant S as Service
  U->>S: request
  S-->>U: response
```

Return JSON:
{
  "content": "# Sequence Diagram\\n\\n```mermaid\\nsequenceDiagram\\n...\\n```"
}""",

    "architecture": """You are an expert system architect. Generate an architecture diagram using Mermaid flowchart.

## Requirements:
1. Identify layers (presentation, business, data)
2. Show module dependencies and interactions
3. Include external services, databases, caches
4. Add descriptions for each component

## Mermaid Syntax:
```mermaid
flowchart TD
  A[Client] --> B[API]
  B --> C[Service]
  C --> D[Database]
```

Return JSON:
{
  "content": "# Architecture\\n\\n```mermaid\\nflowchart\\n...\\n```"
}""",

    "dependencies": """You are an expert software engineer. Document setup and dependencies.

## Requirements:
1. List all build tools (Maven, Gradle, npm, pip, etc.)
2. List external services (DB, Redis, Kafka, etc.)
3. List main libraries/frameworks with versions
4. Include environment setup instructions
5. Include installation and run commands

Return JSON:
{
  "content": "# Setup & Dependencies\\n\\n## Tech Stack\\n...\\n## External Services\\n..."
}""",

    "structure": """You are an expert software architect. Generate an annotated project structure.

## Requirements:
1. Show complete directory tree
2. Annotate each directory with its purpose
3. Group related files together
4. Highlight key files

Return JSON:
{
  "content": "# Project Structure\\n\\n```\\nsrc/\\n  controllers/\\n  ...\\n```\\n\\n## Annotations\\n..."
}""",

    "state_machine": """You are an expert domain modeler. Generate a state machine diagram using Mermaid stateDiagram-v2.

## Requirements:
1. Identify status/state enums in the code
2. Identify state transition logic in services
3. Show all valid states and transitions
4. Include initial and final states
5. Add transition conditions/guards

## Mermaid Syntax:
```mermaid
stateDiagram-v2
  [*] --> PENDING
  PENDING --> CONFIRMED: confirm()
  CONFIRMED --> SHIPPED: ship()
  SHIPPED --> DELIVERED: deliver()
  DELIVERED --> [*]
```

Return JSON:
{
  "content": "# State Machine\\n\\n```mermaid\\nstateDiagram-v2\\n...\\n```"
}""",
}


class ParallelDocumentGenerator:
    """Parallel document generator using asyncio.gather
    
    Generates all 7 technical documents in parallel for performance.
    """
    
    def __init__(
        self,
        api_key: str,
        api_endpoint: str,
        api_version: str,
        deployment_name: str,
    ) -> None:
        """Initialize generator
        
        Args:
            api_key: Azure OpenAI API key
            api_endpoint: Azure OpenAI endpoint
            api_version: API version
            deployment_name: Deployment name
        """
        self._client = AzureOpenAI(
            api_key=api_key,
            api_version=api_version,
            azure_endpoint=api_endpoint,
            azure_deployment=deployment_name,
        )
        self._deployment_name = deployment_name
        
        logger.info(
            f"ParallelDocumentGenerator initialized: endpoint={api_endpoint}, "
            f"deployment={deployment_name}"
        )
    
    def _get_system_prompt(self, document_type: str) -> str:
        """Get system prompt for document type
        
        Args:
            document_type: Type of document
            
        Returns:
            System prompt
        """
        return SYSTEM_PROMPTS.get(document_type, "You are an expert software architect.")
    
    def _get_user_prompt(self, document_type: str, context: str) -> str:
        """Get user prompt for document type
        
        Args:
            document_type: Type of document
            context: Source code context
            
        Returns:
            User prompt
        """
        prompts = {
            "api_spec": f"""Generate API specification from these source files:

{context}

Generate comprehensive API documentation including:
- All endpoints with HTTP methods
- Request/Response schemas with examples
- Headers and query parameters
- Error codes and handling""",
            
            "erd": f"""Generate ERD from these entity files:

{context}

Create entity relationship diagram showing:
- All entities with attributes
- Primary keys and foreign keys
- Relationships with cardinality""",
            
            "sequence": f"""Generate sequence diagram from these service files:

{context}

Create sequence diagram showing:
- Key business logic flows
- Service interactions
- Data flow""",
            
            "architecture": f"""Generate architecture diagram from these configuration and entry point files:

{context}

Create architecture diagram showing:
- Layer structure
- Module dependencies
- External service integrations""",
            
            "dependencies": f"""Generate setup & dependencies document from these config files:

{context}

Document:
- Build tools and commands
- External services
- Required libraries""",
            
            "structure": f"""Generate annotated project structure from all source files:

{context}

Create:
- Complete directory tree
- Annotations for each directory""",
            
            "state_machine": f"""Generate state machine diagram from these enum and service files:

{context}

Create state diagram showing:
- All states
- Valid transitions
- Transition conditions""",
        }
        
        return prompts.get(document_type, f"Generate documentation from:\n\n{context}")
    
    async def _generate_single(
        self,
        document_type: str,
        context: str
    ) -> tuple[str, str]:
        """Generate single document
        
        Args:
            document_type: Type of document
            context: Source code context
            
        Returns:
            Tuple of (document_type, content)
        """
        try:
            system_prompt = self._get_system_prompt(document_type)
            user_prompt = self._get_user_prompt(document_type, context)
            
            response = self._client.chat.completions.create(
                model=self._deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )
            
            result = response.choices[0].message.content
            
            # Parse JSON response
            try:
                parsed = json.loads(result)
                content = parsed.get("content", result)
            except json.JSONDecodeError:
                content = result
            
            logger.info(f"Generated {document_type} successfully")
            return (document_type, content)
            
        except Exception as e:
            logger.error(f"Error generating {document_type}: {e}")
            # Return error placeholder
            return (document_type, f"# Error generating {document_type}\n\n{str(e)}")
    
    async def generate_all(
        self,
        contexts: dict[str, str]
    ) -> dict[str, str]:
        """Generate all 7 documents in parallel using asyncio.gather
        
        Args:
            contexts: Dictionary mapping document_type to source code context
            
        Returns:
            Dictionary mapping document_type to generated content
        """
        logger.info(f"Starting parallel generation of {len(contexts)} documents")
        
        # Create tasks for all documents
        tasks = [
            self._generate_single(doc_type, context)
            for doc_type, context in contexts.items()
        ]
        
        # Execute in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        documents: dict[str, str] = {}
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
                continue
            
            doc_type, content = result
            documents[doc_type] = content
        
        # Handle missing documents
        for doc_type in contexts:
            if doc_type not in documents:
                documents[doc_type] = f"# {doc_type}\n\n(Generation failed)"
        
        logger.info(f"Completed parallel generation: {len(documents)} documents")
        
        return documents
