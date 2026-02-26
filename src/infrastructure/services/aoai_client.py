"""Azure OpenAI 클라이언트 빌더 — ai-agent와 동일한 엔드포인트 분기"""

from __future__ import annotations

from urllib.parse import urlparse
from typing import Any

from openai import AzureOpenAI, OpenAI


def build_aoai_client(
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment: str,
) -> tuple[Any, str]:
    """
    엔드포인트 형태에 따라 OpenAI 또는 AzureOpenAI 클라이언트 반환.
    - api/projects (AI Studio): OpenAI(base_url=models, api_key, default_query api-version)
    - /openai/v1 포함: OpenAI(base_url=endpoint, api_key)
    - 그 외: AzureOpenAI(azure_endpoint, api_key, api_version)
    반환: (client, deployment_name) — create 시 model=deployment_name 사용.
    """
    if not (endpoint and api_key and deployment):
        raise ValueError("Azure OpenAI 설정이 없습니다. AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_DEPLOYMENT를 설정하세요.")

    endpoint = endpoint.rstrip("/")

    # 프로젝트 엔드포인트 (.services.ai.azure.com)
    if "api/projects" in endpoint:
        parsed = urlparse(endpoint)
        models_base = f"{parsed.scheme}://{parsed.netloc}/models"
        client = OpenAI(
            base_url=models_base,
            api_key=api_key,
            default_query={"api-version": api_version or "2024-05-01-preview"},
        )
        return (client, deployment)

    # /openai/v1/ 형태
    if "/openai/v1" in endpoint:
        client = OpenAI(base_url=endpoint, api_key=api_key)
        return (client, deployment)

    # 기존 Azure OpenAI 리소스 엔드포인트
    client = AzureOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version or "2024-06-01",
        azure_deployment=deployment,
    )
    return (client, deployment)
