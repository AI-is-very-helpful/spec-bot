# Spec Bot

Microsoft Teams에서 GitHub 레포지토리 URL을 입력하면, **5개 AI 에이전트**가 레포를 분석해 **5가지 기술 문서**를 자동 생성하고, `.zip` 파일로 다운로드 가능하게 해주는 Teams 봇입니다.

## 주요 기능

- **5가지 기술 문서 자동 생성** (에이전트별 스캐너 → LLM/파서 → 작성기):
  1. **API Specification** (`api_spec.md`) — Controller·REST 엔드포인트 분석
  2. **ERD** (`erd.md` = DBML + 요약) — JPA Entity 기반 엔티티 관계
  3. **Architecture** (`architecture.md`) — 레이어/모듈 구조, Mermaid flowchart
  4. **Tech Stack** (`tech_stack.md`) — 빌드·의존성·설정 파일 기반 기술 스택
  5. **DDL** (`schema.sql`) — JPA Entity 기반 CREATE TABLE 등 DDL

- **ZIP 패키징**: 5개 문서를 하나의 `.zip` 파일로 압축
- **Azure Blob Storage**: ZIP 업로드 및 24시간 유효 SAS URL 발급
- **Adaptive Card**: 프로젝트 요약 + 다운로드 버튼

## 기술 스택

- **Backend**: Azure Functions (Python 3.11+)
- **진입점**: `function_app.py` → `src.presentation.handlers.http_handler.main`
- **Storage**: Azure Blob Storage (ZIP 저장 + SAS URL)
- **AI**: Azure OpenAI Service (에이전트별 LLM 호출)
- **문서 생성**: 프로젝트 내장 **5개 에이전트** (ERD, API, Arch, DDL, Stack) — `src/agents/`
- **Bot**: Microsoft Teams Bot Framework
- **Architecture**: Clean Architecture + Hexagonal
- **Validation**: Pydantic
- **Type Safety**: mypy (strict mode)

## 프로젝트 구조

```
spec-bot/
├── function_app.py                 # Azure Functions 진입점 → http_handler.main
├── host.json                       # Azure Functions 호스트 설정
├── local.settings.json             # 로컬 func 설정 (최소값, 앱 설정은 .env)
├── requirements.txt
├── .env.example
├── run.sh / run.ps1                # 로컬 실행 (func start 래퍼)
│
├── src/
│   ├── domain/                     # 도메인
│   │   ├── entities/               # RepositoryAnalysis 등
│   │   ├── value_objects/          # GitHubURL 등
│   │   └── interfaces/             # GitHubRepository, AIAnalyzer, CardBuilder 등
│   │
│   ├── application/                # 유스 케이스
│   │   ├── dto/
│   │   │   ├── multidoc.py         # 5문서 입출력 DTO
│   │   │   └── repository.py       # 단일 문서 DTO
│   │   └── use_cases/
│   │       ├── multi_doc_analysis.py   # 5문서 생성 UseCase (메인)
│   │       └── analyze_repository.py   # 단일 문서 UseCase
│   │
│   ├── infrastructure/             # 인프라
│   │   ├── repositories/
│   │   │   └── github.py           # PyGitHubRepository (메타데이터 조회)
│   │   └── services/
│   │       ├── ai_agent_pipeline.py    # 5개 에이전트 오케스트레이션 (문서 생성)
│   │       ├── blob_storage.py         # Blob 업로드, SAS URL
│   │       ├── zip_packager.py         # 5개 파일 ZIP 패키징
│   │       ├── card.py                 # TeamsCardBuilder (Adaptive Card)
│   │       ├── teams_bot.py            # Teams 메시지 파싱/도움말
│   │       ├── aoai_client.py          # Azure OpenAI 클라이언트 빌더
│   │       ├── logging_config.py
│   │       └── ...
│   │
│   ├── agents/                     # 5개 AI 에이전트 (문서 생성)
│   │   ├── erd_agent/              # ERD → database.dbml, erd_summary.md
│   │   ├── api_agent/              # API 스펙 → api_spec.md
│   │   ├── arch_agent/             # 아키텍처 → architecture.md
│   │   ├── ddl_agent/              # DDL → schema.sql
│   │   └── stack_agent/            # 기술 스택 → tech_stack.md
│   │
│   └── presentation/
│       └── handlers/
│           └── http_handler.py    # HTTP 트리거 핸들러 (POST /api/messages)
│
├── tests/unit/                     # 단위 테스트
├── docs/                           # 상세 문서
│   ├── ARCHITECTURE.md             # 아키텍처 개요
│   ├── LOGIC_FLOW.md               # 요청→응답 로직 흐름
│   ├── FLOW_FOR_PPT.md             # PPT용 슬라이드 구조
│   ├── AGENT_FLOWS.md              # 에이전트별 스캐너→추출기→작성기 흐름
│   └── BLOB_LIFECYCLE.md           # Blob 업로드/만료 정책
│
├── mypy.ini
├── pytest.ini
└── PRD.md
```

## 문서 참고

| 문서 | 내용 |
|------|------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 레이어 구성, 파이프라인 개요 |
| [LOGIC_FLOW.md](docs/LOGIC_FLOW.md) | 진입점 → 유스케이스 → 5 에이전트 → ZIP/Blob 상세 |
| [FLOW_FOR_PPT.md](docs/FLOW_FOR_PPT.md) | Azure Function 수신 ~ 응답까지 PPT용 슬라이드 |
| [AGENT_FLOWS.md](docs/AGENT_FLOWS.md) | 에이전트별 스캔 기준(어노테이션/파일명) → 추출기 → 작성기 |
| [BLOB_LIFECYCLE.md](docs/BLOB_LIFECYCLE.md) | Blob 업로드·SAS·만료 |

## 의존성 설치

### 시스템 Python (Azure Functions 로컬 실행)

```bash
pip install -r requirements.txt
```

### 가상환경 (테스트·타입 검사)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt pytest pytest-mock pytest-cov mypy
```

## 환경 설정

1. `.env.example`을 `.env`로 복사 후 편집:

```bash
cp .env.example .env
```

2. `.env` 필수 항목 예시:

```bash
# Azure Bot
AZURE_BOT_ID=your_bot_app_id
AZURE_BOT_PASSWORD=your_bot_app_password

# Azure OpenAI (에이전트 LLM 호출)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_key
OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT=your-deployment-name

# Blob Storage (ZIP 저장)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# GitHub (Public 레포는 생략 가능)
# GITHUB_TOKEN=your_github_pat
```

로컬에서는 **`.env`만** 채우면 되며, `local.settings.json`은 Azure Functions Core Tools용 최소 설정만 두면 됩니다.

## 로컬 실행

```bash
./run.sh
# 또는
func start
```

`POST /api/messages` 로 Teams Activity 형식 JSON을 보내면 동일 흐름으로 동작합니다.

## 테스트

```bash
source .venv/bin/activate
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

## 타입 검사

```bash
mypy src/
```

## Azure 배포

### 1. 리소스 준비

- Azure Storage Account + Blob 컨테이너 (ZIP 저장용)
- Azure Bot Service (Teams 채널 연동)
- Azure OpenAI 리소스 + 배포

### 2. Function App 생성

```bash
az functionapp create \
  --resource-group <rg> \
  --name <your-spec-bot> \
  --storage-account <storage> \
  --consumption-plan-location koreacentral \
  --runtime python --runtime-version 3.11 --os-type linux
```

### 3. App Settings 등록

```bash
az functionapp config appsettings set \
  --name <your-spec-bot> --resource-group <rg> \
  --settings \
  AZURE_BOT_ID="<bot_id>" \
  AZURE_BOT_PASSWORD="<bot_password>" \
  AZURE_STORAGE_CONNECTION_STRING="<connection_string>" \
  AZURE_OPENAI_ENDPOINT="<openai_endpoint>" \
  AZURE_OPENAI_API_KEY="<api_key>" \
  OPENAI_API_VERSION="2024-12-01-preview" \
  AZURE_OPENAI_DEPLOYMENT="<deployment_name>"
```

### 4. 배포 및 Bot 연결

```bash
func azure functionapp publish <your-spec-bot>
```

Azure Bot → Configuration → Messaging endpoint:  
`https://<your-spec-bot>.azurewebsites.net/api/messages`

## 사용법

Teams에서:

```
@Spec Bot https://github.com/owner/repo
```

- 분석 시작 안내 후, 5개 문서가 ZIP으로 Blob에 업로드되고 SAS URL이 포함된 Adaptive Card가 옵니다.
- **[📦 기술 문서 패키지 다운로드 (.zip)]** 버튼으로 다운로드합니다.

## 생성되는 문서 (5개)

| 파일 | 설명 |
|------|------|
| `api_spec.md` | REST API 명세 (Controller·엔드포인트) |
| `erd.md` | ERD 요약 + DBML (JPA Entity 기반) |
| `architecture.md` | 아키텍처 스타일·레이어·Mermaid flowchart |
| `tech_stack.md` | 언어·프레임워크·의존성 (빌드/설정 파일 기반) |
| `schema.sql` | DDL (JPA Entity 기반 CREATE TABLE 등) |

## 아키텍처 요약

```
[Teams] → POST /api/messages → function_app → http_handler.main
    → MultiDocumentAnalysisUseCase.execute()
        → fetch_metadata (Blob 이름용)
        → ai_analyzer.run_from_url()  ← prepare_repo(zip) + 5 agents
        → ZIP 패키징 → Blob 업로드 → SAS URL
    → build_download_card → HTTP 200 + Adaptive Card JSON
```

에이전트별 **스캐너(어떤 파일/어노테이션)** → **추출기(LLM 또는 파서)** → **작성기** 흐름은 [AGENT_FLOWS.md](docs/AGENT_FLOWS.md) 참고.

## 라이선스

MIT
