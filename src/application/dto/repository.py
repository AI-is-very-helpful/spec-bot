"""Application layer - DTOs"""

from dataclasses import dataclass
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AnalyzeRepositoryInput(BaseModel):
    """Input DTO for analyze repository use case"""
    github_url: str = Field(..., description="GitHub repository URL")
    
    @field_validator("github_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v:
            raise ValueError("GitHub URL cannot be empty")
        if "github.com" not in v:
            raise ValueError("Invalid GitHub URL")
        return v.strip().rstrip("/")


class AnalyzeRepositoryOutput(BaseModel):
    """Output DTO for analyze repository use case"""
    card: dict = Field(..., description="Adaptive Card JSON")
    api_spec: str = Field(..., description="API specification markdown")
    erd_image_url: str = Field(..., description="ERD image URL")
    sequence_image_url: str = Field(..., description="Sequence diagram image URL")
    summary: dict = Field(..., description="Project summary")
    insights: list[str] = Field(..., description="Key insights")


class ErrorOutput(BaseModel):
    """Error response DTO"""
    error: str
    message: str
