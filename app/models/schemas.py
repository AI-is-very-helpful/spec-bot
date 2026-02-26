"""Pydantic models for structured output"""
from typing import Optional

from pydantic import BaseModel, Field


class APIEndpoint(BaseModel):
    """개별 API 엔드포인트 정보"""
    path: str = Field(description="API 경로")
    method: str = Field(description="HTTP 메서드 (GET, POST, PUT, DELETE 등)")
    summary: str = Field(description="엔드포인트 요약")
    description: Optional[str] = Field(default=None, description="상세 설명")
    request_params: Optional[list[str]] = Field(default=None, description="요청 파라미터")
    request_body: Optional[str] = Field(default=None, description="요청 바디 스키마")
    response: Optional[str] = Field(default=None, description="응답 스키마")


class ProjectSummary(BaseModel):
    """프로젝트 요약 정보"""
    name: str = Field(description="프로젝트 이름")
    purpose: str = Field(description="프로젝트 목적")
    tech_stack: list[str] = Field(description="사용 기술 스택")
    architecture: str = Field(description="아키텍처 유형")
    folder_structure: list[str] = Field(description="주요 폴더 구조")


class AnalysisResult(BaseModel):
    """AI 분석 결과 전체"""
    project_summary: ProjectSummary = Field(description="프로젝트 요약")
    api_spec: str = Field(description="API 스펙 (Markdown 형식)")
    erd_code: str = Field(description="Mermaid ERD 코드")
    sequence_code: str = Field(description="Mermaid 시퀀스 다이어그램 코드")
    key_insights: list[str] = Field(description="주요 발견 사항")
