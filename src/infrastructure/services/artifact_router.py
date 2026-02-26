"""Infrastructure - Artifact Router (Intelligent File Routing for 7 Document Types)"""

import logging
import re
from dataclasses import dataclass
from typing import Optional

from src.domain.entities.repository import FileType, SourceFile

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DocumentRoute:
    """Document route configuration"""
    name: str
    description: str
    preferred_file_types: tuple[FileType, ...]
    key_patterns: tuple[str, ...]


# Document route configurations
API_SPEC_ROUTE = DocumentRoute(
    name="api_spec",
    description="API Specification (OpenAPI 3.0)",
    preferred_file_types=(FileType.CONTROLLER, FileType.ENTITY),
    key_patterns=("controller", "router", "route", "handler", "endpoint", "api", "dto", "request", "response"),
)

ERD_ROUTE = DocumentRoute(
    name="erd",
    description="Entity Relationship Diagram",
    preferred_file_types=(FileType.ENTITY,),
    key_patterns=("entity", "model", "schema", "table", "database", "migration"),
)

SEQUENCE_ROUTE = DocumentRoute(
    name="sequence",
    description="Sequence Diagram",
    preferred_file_types=(FileType.SERVICE,),
    key_patterns=("service", "business", "usecase", "logic", "flow", "process"),
)

ARCHITECTURE_ROUTE = DocumentRoute(
    name="architecture",
    description="Architecture Diagram",
    preferred_file_types=(FileType.ENTRYPOINT, FileType.CONFIG, FileType.REPOSITORY),
    key_patterns=("main", "app", "server", "config", "setup", "di", "container", "module"),
)

DEPENDENCIES_ROUTE = DocumentRoute(
    name="dependencies",
    description="Setup & Dependencies",
    preferred_file_types=(FileType.CONFIG,),
    key_patterns=("pom.xml", "build.gradle", "requirements.txt", "package.json", "docker", "gemfile", "go.mod"),
)

STRUCTURE_ROUTE = DocumentRoute(
    name="structure",
    description="Project Structure",
    preferred_file_types=(
        FileType.CONTROLLER, FileType.SERVICE, FileType.ENTITY,
        FileType.CONFIG, FileType.ENTRYPOINT, FileType.REPOSITORY
    ),
    key_patterns=(),
)

STATE_MACHINE_ROUTE = DocumentRoute(
    name="state_machine",
    description="State Machine Diagram",
    preferred_file_types=(FileType.ENTITY, FileType.SERVICE),
    key_patterns=("enum", "status", "state", "lifecycle", "transition", "workflow", "fsm"),
)


class ArtifactRouter:
    """Intelligent file router for 7 document types
    
    Routes source files to the appropriate document type based on:
    - File type classification (CONTROLLER, SERVICE, ENTITY, etc.)
    - File name patterns
    - Document type requirements
    """
    
    def __init__(self) -> None:
        """Initialize artifact router"""
        self._routes: dict[str, DocumentRoute] = {
            "api_spec": API_SPEC_ROUTE,
            "erd": ERD_ROUTE,
            "sequence": SEQUENCE_ROUTE,
            "architecture": ARCHITECTURE_ROUTE,
            "dependencies": DEPENDENCIES_ROUTE,
            "structure": STRUCTURE_ROUTE,
            "state_machine": STATE_MACHINE_ROUTE,
        }
    
    def _filter_by_file_type(
        self,
        files: list[SourceFile],
        file_type: FileType
    ) -> list[SourceFile]:
        """Filter files by type
        
        Args:
            files: List of source files
            file_type: Target file type
            
        Returns:
            Filtered files
        """
        return [f for f in files if f.file_type == file_type]
    
    def _filter_by_pattern(
        self,
        files: list[SourceFile],
        patterns: tuple[str, ...]
    ) -> list[SourceFile]:
        """Filter files by name patterns
        
        Args:
            files: List of source files
            patterns: Tuple of regex patterns
            
        Returns:
            Filtered files
        """
        if not patterns:
            return files
        
        result: list[SourceFile] = []
        for file in files:
            path_lower = file.path.lower()
            for pattern in patterns:
                if re.search(pattern, path_lower):
                    result.append(file)
                    break
        
        return result
    
    def _combine_filters(
        self,
        files: list[SourceFile],
        file_types: tuple[FileType, ...],
        patterns: tuple[str, ...]
    ) -> list[SourceFile]:
        """Combine file type and pattern filters
        
        Args:
            files: List of source files
            file_types: Required file types
            patterns: Required patterns
            
        Returns:
            Filtered files
        """
        # First filter by type
        if file_types:
            type_filtered: list[SourceFile] = []
            for ft in file_types:
                type_filtered.extend(self._filter_by_file_type(files, ft))
        else:
            type_filtered = files
        
        # Then filter by pattern
        if patterns:
            return self._filter_by_pattern(type_filtered, patterns)
        
        return type_filtered
    
    def route_to_api_spec(self, files: list[SourceFile]) -> list[SourceFile]:
        """Route files for API Specification
        
        Args:
            files: All source files
            
        Returns:
            Files routed for API spec
        """
        route = self._routes["api_spec"]
        return self._combine_filters(files, route.preferred_file_types, route.key_patterns)
    
    def route_to_erd(self, files: list[SourceFile]) -> list[SourceFile]:
        """Route files for ERD
        
        Args:
            files: All source files
            
        Returns:
            Files routed for ERD
        """
        route = self._routes["erd"]
        return self._combine_filters(files, route.preferred_file_types, route.key_patterns)
    
    def route_to_sequence(self, files: list[SourceFile]) -> list[SourceFile]:
        """Route files for Sequence Diagram
        
        Args:
            files: All source files
            
        Returns:
            Files routed for Sequence
        """
        route = self._routes["sequence"]
        return self._combine_filters(files, route.preferred_file_types, route.key_patterns)
    
    def route_to_architecture(self, files: list[SourceFile]) -> list[SourceFile]:
        """Route files for Architecture Diagram
        
        Args:
            files: All source files
            
        Returns:
            Files routed for Architecture
        """
        route = self._routes["architecture"]
        return self._combine_filters(files, route.preferred_file_types, route.key_patterns)
    
    def route_to_dependencies(self, files: list[SourceFile]) -> list[SourceFile]:
        """Route files for Dependencies document
        
        Args:
            files: All source files
            
        Returns:
            Files routed for Dependencies
        """
        route = self._routes["dependencies"]
        
        # For dependencies, prioritize config files by exact name match
        config_files = self._filter_by_file_type(files, FileType.CONFIG)
        
        # Also include patterns
        pattern_files = self._filter_by_pattern(files, route.key_patterns)
        
        # Combine and deduplicate
        seen = set()
        result: list[SourceFile] = []
        for f in config_files + pattern_files:
            if f.path not in seen:
                seen.add(f.path)
                result.append(f)
        
        return result
    
    def route_to_structure(self, files: list[SourceFile]) -> list[SourceFile]:
        """Route files for Structure document
        
        Args:
            files: All source files
            
        Returns:
            Files routed for Structure (all files)
        """
        route = self._routes["structure"]
        return self._combine_filters(files, route.preferred_file_types, ())
    
    def route_to_state_machine(self, files: list[SourceFile]) -> list[SourceFile]:
        """Route files for State Machine Diagram
        
        Args:
            files: All source files
            
        Returns:
            Files routed for State Machine
        """
        route = self._routes["state_machine"]
        return self._combine_filters(files, route.preferred_file_types, route.key_patterns)
    
    def route_all(self, files: list[SourceFile]) -> dict[str, list[SourceFile]]:
        """Route files to all 7 document types
        
        Args:
            files: All source files
            
        Returns:
            Dictionary mapping document type to routed files
        """
        return {
            "api_spec": self.route_to_api_spec(files),
            "erd": self.route_to_erd(files),
            "sequence": self.route_to_sequence(files),
            "architecture": self.route_to_architecture(files),
            "dependencies": self.route_to_dependencies(files),
            "structure": self.route_to_structure(files),
            "state_machine": self.route_to_state_machine(files),
        }
    
    def build_context_for_document(
        self,
        files: list[SourceFile],
        document_type: str,
        max_chars: int = 8000
    ) -> str:
        """Build context string for a specific document
        
        Args:
            files: Routed files for this document
            document_type: Type of document
            max_chars: Maximum characters in context
            
        Returns:
            Context string for LLM
        """
        context_parts: list[str] = []
        total_chars = 0
        
        for file in files:
            if total_chars >= max_chars:
                break
            
            file_content = f"\n### File: {file.path} (Type: {file.file_type.value})\n"
            file_content += f"```\n{file.content}\n```\n"
            
            # Check if adding this would exceed limit
            if total_chars + len(file_content) > max_chars:
                remaining = max_chars - total_chars
                if remaining > 100:
                    file_content = file_content[:remaining]
                else:
                    break
            
            context_parts.append(file_content)
            total_chars += len(file_content)
        
        return "\n".join(context_parts)
