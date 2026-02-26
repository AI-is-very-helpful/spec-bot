# Spec Bot — 아키텍처 문서

## 개요

Spec Bot은 Teams에서 GitHub 레포 URL을 입력받아 Azure OpenAI로 소스코드를 분석해 **7가지 기술 문서**를 자동 생성하고, ZIP으로 패키징해 Blob Storage에 올린 뒤 SAS URL과 함께 Adaptive Card로 전달하는 Teams 봇입니다.
진입부는 Azure Functions(HTTP / Bot 메시지)이며, 비즈니스 흐름은 Clean Architecture 레이어(도메인 · 애플리케이션 · 인프라)로 구성됩니다. **요청부터 응답까지 단계별 로직은 [LOGIC_FLOW.md](LOGIC_FLOW.md) 참고.**

## 아키텍처 스타일

**Clean Architecture + Hexagonal** — 프레젠테이션(HTTP/Bot)은 유스 케이스만 호출하고, 도메인은 인터페이스(포트)만 정의하며, GitHub·OpenAI·Blob·ZIP·Teams 등 외부 연동은 인프라 어댑터로 주입됩니다.

## 구성

```
┌─────────────────────────────────────────────────────┐
│              Presentation Layer                      │
│   function_app.py · http_handler · Bot /api/messages │
└──────────┬────────────────────────────┬────────────┘
           │                             │
     ┌─────▼──────────────┐     ┌────────▼────────────┐
     │ application/        │     │ domain/             │
     │ dto/                │     │ entities/           │
     │ use_cases/          │◄────│ value_objects/      │
     │  analyze_repository │     │ interfaces/ (Ports)  │
     │  multi_doc_analysis │     └────────┬────────────┘
     └─────┬──────────────┘              │
           │                             │
     ┌─────▼─────────────────────────────▼────────────┐
     │ infrastructure/                                │
     │ repositories/github.py   · services/           │
     │   openai · multi_doc_analyzer · mermaid        │
     │   blob_storage · zip_packager · card · teams_bot│
     └───────────────────────────────────────────────┘
```

## 생성 문서별 파이프라인

전체 흐름은 동일한 5단계를 따릅니다:

```
1. GitHub URL 수신        — Teams/Bot 또는 HTTP Body
2. 레포 준비              — ai-agent `prepare_repo`로 zip 다운로드/로컬 경로 확보
3. AI 분석 (ai-agent)     — 5개 에이전트(ERD, API, Arch, DDL, Stack)가 관련 파일만 스캔/분석해 7문서 생성
4. ZIP 패키징 · Blob 업로드 — zip_packager → blob_storage, SAS URL 발급
5. Adaptive Card 반환    — card_builder로 요약 + 다운로드 버튼
```

### API Specification
- 입력: 레포 소스 파일(Controller·라우트 등)
- 출력: `api_spec.md` (OpenAPI 3.0 규격 Markdown)

### ERD
- 입력: 엔티티·관계 관련 소스
- 출력: `erd.md` (Mermaid erDiagram)

### Sequence Diagram
- 입력: 비즈니스 로직·호출 흐름 관련 소스
- 출력: `sequence.md` (Mermaid sequenceDiagram)

### Architecture Diagram
- 입력: 구조·설정·모듈 구분 관련 소스
- 출력: `architecture.md` (Mermaid flowchart)

### Setup & Dependencies
- 입력: 빌드 파일·의존성·외부 서비스 설정
- 출력: `dependencies.md`

### Project Structure
- 입력: 파일 트리 + 선택 소스
- 출력: `structure.md` (디렉터리 트리 + AI 주석)

### State Machine
- 입력: 도메인 생명주기·상태 관련 소스
- 출력: `state_machine.md` (Mermaid stateDiagram)

## 공용 모듈 (도메인 · 애플리케이션 · 인프라)

| 모듈 | 역할 |
|------|------|
| `domain/entities/repository.py` | SourceFile, RepositoryAnalysis, RepositoryMetadata |
| `domain/value_objects/github.py` | GitHubURL, FilePath, SourceCode |
| `domain/interfaces/repositories.py` | GitHubRepository, AIAnalyzer, CardBuilder, DiagramRenderer 등 포트 |
| `application/dto/repository.py` | 단일 문서 분석 입·출력 DTO |
| `application/dto/multidoc.py` | 5문서 분석 입·출력 DTO (MultiDocumentAnalysisInput/Output) |
| `application/use_cases/multi_doc_analysis.py` | 5문서 생성 유스 케이스 (fetch → AI → ZIP → Blob → Card) |
| `infrastructure/repositories/github.py` | GitHub API/스크래핑 구현 (GitHubRepository 구현체) |
| `infrastructure/services/openai.py` | Azure OpenAI 호출 (AIAnalyzer 구현체) |
| `infrastructure/services/multi_doc_analyzer.py` | 7문서 일괄 AI 분석 (현재 미사용, ai-agent만 사용) |
| `infrastructure/services/blob_storage.py` | Blob 업로드 및 SAS URL 발급 |
| `infrastructure/services/zip_packager.py` | 5개 파일 ZIP 패키징 |
| `infrastructure/services/card.py` | Teams Adaptive Card 빌드 (CardBuilder 구현체) |
| `infrastructure/services/ai_agent_pipeline.py` | agents(erd/api/arch/ddl/stack) 실행 → 5 doc 반환 |
| `src/agents/` | 포함된 ai-agent 패키지 (erd_agent, api_agent, arch_agent, ddl_agent, stack_agent) |

## agents(ai-agent) 내부 로직 (기본)

Azure Function·Teams 인터페이스는 동일하게 두고, **문서 생성 방식만** 프로젝트 내 포함된 agents로 바꿀 수 있다.

- **동작**: GitHub URL → `prepare_repo`(zip 다운로드) → **src/agents** 아래 5개 에이전트(ERD, API, Arch, DDL, Stack) 실행 → 5개 문서만 반환 → ZIP·Blob·Card 동일.
- **코드 위치**: ai-agent 코드는 **spec-bot 프로젝트에 포함** (`src/agents/`). 별도 ai-agent 프로젝트/경로 불필요.
- **의존성**: requirements.txt에 javalang·rich 등 agents용 의존성 포함.

## 확장 방법

새 문서 유형을 추가하려면:

1. `application/dto/multidoc.py`에 새 문서 파일명을 `DOCUMENT_FILES` 등에 추가
2. `src/agents/`에 새 에이전트를 추가하거나, 기존 에이전트 산출물을 확장
3. 필요 시 `domain/interfaces/repositories.py`에 전용 포트를 두고, 인프라에서 구현
4. ZIP 패키징 시 새 파일이 포함되도록 `zip_packager` 로직 반영
