"""Infrastructure - ai-agent 파이프라인 어댑터 (GitHub URL → prepare_repo → 5 agents → 5 doc)"""

import json
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

from src.domain.entities.repository import RepositoryAnalysis
from src.domain.interfaces.repositories import AIAnalyzer

logger = logging.getLogger(__name__)

# 프로젝트 내 포함된 agents 패키지 경로 (src/agents — erd_agent, api_agent 등)
_AGENTS_ROOT = Path(__file__).resolve().parent.parent.parent / "agents"


def _read_file(path: Path, max_chars: int = 100_000) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    return text[:max_chars] + "\n\n... (truncated)" if len(text) > max_chars else text


class AiAgentPipelineAdapter(AIAnalyzer):
    """
    프로젝트 내 포함된 ai-agent 코드(erd_agent, api_agent, arch_agent, ddl_agent, stack_agent)로 분석.
    - GitHub URL → prepare_repo(zip 다운로드) → 5개 에이전트 실행 → 5개 문서만 반환.
    - 외부 경로/연결 없이 src/agents 아래 패키지만 사용.
    """

    def analyze(self, analysis: RepositoryAnalysis) -> str:
        """AIAnalyzer 인터페이스: RepositoryAnalysis는 사용하지 않고 url만 사용."""
        doc_data = self.run_from_url(analysis.url.value)
        return json.dumps(doc_data, ensure_ascii=False)

    def run_from_url(self, github_url: str) -> dict[str, Any]:
        """
        GitHub URL(https://github.com/...)을 받아 ai-agent prepare_repo로 레포 준비 후 5개 에이전트 실행.
        prepare_repo는 GitHub면 zip 다운로드, 로컬 경로면 그대로 사용. 5개 문서 dict 반환.
        """
        out_root = Path(tempfile.mkdtemp(prefix="specbot_aiagent_"))
        cache_dir = out_root / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # erd_agent.config.settings가 import 시점에 env를 읽으므로, import 전에 설정
        os.environ["DOC_OUTPUT_DIR"] = str(out_root)
        os.environ["CACHE_DIR"] = str(cache_dir)
        if not _AGENTS_ROOT.is_dir():
            raise RuntimeError(
                f"agents 디렉터리가 없습니다: {_AGENTS_ROOT}. "
                "src/agents 아래에 erd_agent, api_agent, arch_agent, ddl_agent, stack_agent가 있어야 합니다."
            )
        agents_path = str(_AGENTS_ROOT)
        if agents_path not in sys.path:
            sys.path.insert(0, agents_path)

        try:
            from erd_agent.repo import prepare_repo
            from erd_agent.commands.erd import run_erd
            from api_agent.run import run_api
            from arch_agent.run import run_arch
            from ddl_agent.run import run_ddl
            from stack_agent.run import run_stack
        except ImportError as e:
            logger.exception("agents 패키지 로드 실패 (src/agents). 의존성 확인 필요.")
            raise RuntimeError(
                f"erd_agent/api_agent 등 로드 실패: {e}. "
                "requirements.txt에 javalang, rich 등 ai-agent 의존성이 있는지 확인하세요."
            ) from e

        logger.info("Running ai-agent pipeline (prepare_repo + 5 agents)", extra={"repo_url": github_url})

        try:
            repo_path = prepare_repo(github_url)
        except Exception as e:
            logger.exception("prepare_repo failed")
            raise RuntimeError(f"레포 준비 실패( zip 다운로드/접근 ): {e}") from e

        agents = [
            ("erd", run_erd, out_root / "erd"),
            ("api", run_api, out_root / "api"),
            ("arch", run_arch, out_root / "arch"),
            ("ddl", run_ddl, out_root / "ddl"),
            ("stack", run_stack, out_root / "stack"),
        ]

        for name, fn, out_dir in agents:
            out_dir.mkdir(parents=True, exist_ok=True)
            try:
                fn(repo=str(repo_path), out_dir=out_dir)
            except Exception as e:
                logger.warning("Agent %s failed: %s", name, e, exc_info=True)

        # 산출물 수집 — 5개 에이전트 결과만 반환 (7 doc 매핑 없음)
        doc_data = self._collect_documents(out_root, repo_path.name)
        return doc_data

    def _collect_documents(self, out_root: Path, repo_name: str) -> dict[str, Any]:
        """에이전트 산출물만 읽어 5개 문서 + project_summary dict 구성."""
        api_spec = _read_file(out_root / "api" / "api_spec.md")
        erd_summary = _read_file(out_root / "erd" / "erd_summary.md")
        dbml = _read_file(out_root / "erd" / "database.dbml")
        erd_content = f"# ERD\n\n{erd_summary}\n\n## DBML\n\n```dbml\n{dbml}\n```" if dbml else f"# ERD\n\n{erd_summary}"
        architecture = _read_file(out_root / "arch" / "architecture.md")
        tech_stack = _read_file(out_root / "stack" / "tech_stack.md")
        schema_sql = _read_file(out_root / "ddl" / "schema.sql")

        summary = {
            "name": repo_name,
            "purpose": "",
            "tech_stack": [],
            "architecture": "",
            "folder_structure": [],
        }

        return {
            "project_summary": summary,
            "api_spec": api_spec or "# API Specification\n\n(No API spec generated.)",
            "erd": erd_content or "# ERD\n\n(No ERD generated.)",
            "architecture": architecture or "# Architecture\n\n(No architecture doc generated.)",
            "tech_stack": tech_stack or "# Tech Stack\n\n(No tech stack generated.)",
            "schema_sql": schema_sql or "-- No DDL generated.",
        }
