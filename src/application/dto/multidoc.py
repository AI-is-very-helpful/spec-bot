"""Application layer - Multi-Document DTOs"""

from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class MultiDocumentAnalysisInput(BaseModel):
    """Input DTO for multi-document analysis use case"""
    github_url: str = Field(..., description="GitHub repository URL")
    
    @field_validator("github_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v:
            raise ValueError("GitHub URL cannot be empty")
        if "github.com" not in v:
            raise ValueError("Invalid GitHub URL - must be github.com")
        return v.strip().rstrip("/")


class DocumentPackage(BaseModel):
    """Package containing all 7 generated documents"""
    api_spec: str = Field(default="", description="API Specification in Markdown")
    erd: str = Field(default="", description="ERD with Mermaid erDiagram")
    sequence: str = Field(default="", description="Sequence Diagram with Mermaid")
    architecture: str = Field(default="", description="Architecture Diagram with Mermaid flowchart")
    dependencies: str = Field(default="", description="Setup & Dependencies document")
    structure: str = Field(default="", description="Annotated Project Structure")
    state_machine: str = Field(default="", description="State Machine Diagram with Mermaid stateDiagram")
    
    def keys(self) -> list[str]:
        """Return document file names"""
        return [
            "api_spec.md",
            "erd.md",
            "sequence.md",
            "architecture.md",
            "dependencies.md",
            "structure.md",
            "state_machine.md"
        ]
    
    def values(self) -> list[str]:
        """Return document contents"""
        return [
            self.api_spec,
            self.erd,
            self.sequence,
            self.architecture,
            self.dependencies,
            self.structure,
            self.state_machine
        ]
    
    def __len__(self) -> int:
        return 7
    
    def __iter__(self):
        return iter(self.items())
        """Return document name-content pairs"""
        return list(zip(self.keys(), self.values()))
    
    def __iter__(self) -> tuple[str, str]:
        return iter(self.items())


class MultiDocumentAnalysisOutput(BaseModel):
    """Output DTO for multi-document analysis use case"""
    zip_blob_url: str = Field(..., description="Blob Storage URL with SAS token for ZIP download")
    summary: dict[str, Any] = Field(..., description="Project summary")
    document_count: int = Field(..., description="Number of documents generated")
    expires_in_seconds: int = Field(default=86400, description="SAS URL expiry time (24 hours default)")
    
    @field_validator("document_count")
    @classmethod
    def validate_count(cls, v: int) -> int:
        if v != 7:
            raise ValueError(f"Expected 7 documents, got {v}")
        return v
    
    @field_validator("expires_in_seconds")
    @classmethod
    def validate_expiry(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("Expiry must be positive")
        if v > 86400 * 7:  # Max 7 days
            raise ValueError("Expiry cannot exceed 7 days")
        return v
