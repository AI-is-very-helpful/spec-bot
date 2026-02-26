# Spec Bot 아키텍처 및 동작 흐름

## 1. 프로젝트 개요

Spec Bot은 Microsoft Teams에서 GitHub 레포지토리 URL을 입력하면 AI가 자동으로 7가지 핵심 기술 문서를 생성하고 ZIP 파일로 다운로드 가능한 Teams 에이전트입니다.

### 주요 기능
- 7가지 기술 문서 자동 생성 (API Spec, ERD, Sequence, Architecture, Dependencies, Structure, State Machine)
- ZIP 패키징 및 Azure Blob Storage 업로드
- 24시간 유효 SAS URL 발급
- Adaptive Card를 통한 결과 전송

---

## 2. 시스템 아키텍처

### 2.1 기술 스택

| 구성요소 | 기술 |
|---------|------|
| Interface | Microsoft Teams |
| Bot Framework | Azure Bot Service |
| Backend | Azure Functions (Python 3.11+) |
| Storage | Azure Blob Storage |
| AI | Azure OpenAI Service (kimi-k2.5) |
| Validation | Pydantic |
| Type Safety | mypy (strict mode) |
| Architecture | Clean Architecture + Hexagonal Architecture |

### 2.2 레이어드 아키텍처

```
┌─────────────────────────────────────────────────────────┐
│              Presentation Layer (API)                    │
│         HTTP Handler (Azure Functions Trigger)           │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│              Application Layer (Use Cases)               │
│      MultiDocumentAnalysisUseCase, DTOs                 │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                Domain Layer (Core)                       │
│  Entities, Value Objects, Interfaces (Ports)           │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│            Infrastructure Layer (Adapters)               │
│  GitHub, OpenAI, Blob Storage, Teams, ZIP Packager    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 프로젝트 구조

```
spec-bot/
├── function_app.py                 # Azure Functions 엔트리 포인트
│
├── app/                            # 기존 구조 (레거시 호환)
│   ├── main.py                     # Teams 메시지 핸들러
│   ├── config.py                   # 설정 관리
│   ├── services/
│   │   ├── github.py               # GitHub 스크래핑
│   │   ├── openai_service.py       # OpenAI 서비스
│   │   ├── mermaid_renderer.py     # Mermaid 렌더링
│   │   └── adaptive_card.py        # Adaptive Card 빌더
│   └── models/
│       └── schemas.py              # Pydantic 스키마
│
├── src/                            # Clean Architecture 핵심 코드
│   ├── domain/                     # 도메인 레이어
│   │   ├── entities/
│   │   │   └── repository.py      # SourceFile, RepositoryAnalysis, RepositoryMetadata
│   │   ├── value_objects/
│   │   │   └── github.py           # GitHubURL, FilePath, SourceCode
│   │   └── interfaces/
│   │       └── repositories.py    # 포트 인터페이스 (GitHubRepository, AIAnalyzer, CardBuilder)
│   │
│   ├── application/                # 애플리케이션 레이어
│   │   ├── dto/
│   │   │   ├── repository.py       # 단일 문서 DTO
│   │   │   └── multidoc.py         # 7문서 DTO (MultiDocumentAnalysisInput/Output)
│   │   └── use_cases/
│   │       ├── analyze_repository.py   # 단일 문서 UseCase
│   │       └── multi_doc_analysis.py   # 7문서 UseCase
│   │
│   ├── infrastructure/             # 인프라스트럭처 레이어
│   │   ├── repositories/
│   │   │   └── github.py           # PyGitHubRepository 구현
│   │   └── services/
│   │       ├── openai.py           # AzureOpenAIService
│   │       ├── multi_doc_analyzer.py   # 7문서 AI 분석
│   │       ├── mermaid.py          # MermaidInkRenderer
│   │       ├── card.py             # TeamsCardBuilder
│   │       ├── blob_storage.py     # Azure Blob Storage
│   │       ├── zip_packager.py     # ZIP 패키징
│   │       ├── teams_bot.py        # Teams Bot Service
│   │       └── logging_config.py  # 로깅 설정
│   │
│   └── presentation/               # 프레젠테이션 레이어
│       └── handlers/
│           └── http_handler.py      # Azure Functions HTTP Trigger
│
├── tests/                          # 테스트 (TDD)
│   └── unit/
│       ├── domain/                 # 도메인 테스트
│       ├── application/            # 애플리케이션 테스트
│       └── infrastructure/         # 인프라스트럭처 테스트
│
├── host.json                       # Azure Functions 설정
├── requirements.txt                # Python 의존성
├── mypy.ini                        # mypy 타입 검사 설정
└── .env.example                    # 환경변수 예시
```

---

## 4. 데이터 흐름 (Data Flow)

### 4.1 전체 흐름도

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Teams     │────▶│ Azure Bot    │────▶│    Azure        │
│   User      │     │  Service     │     │  Functions      │
└─────────────┘     └──────────────┘     └────────┬────────┘
                                                   │
                    ┌──────────────────────────────▼─────────────────────────┐
                    │              HTTP Handler (http_handler.py)           │
                    │  1. Teams Activity 파싱                               │
                    │  2. GitHub URL 추출                                  │
                    │  3. Input Validation (Pydantic)                     │
                    └──────────────────────────────┬────────────────────────┘
                                                   │
                    ┌───────────────────────────────▼────────────────────────┐
                    │         MultiDocumentAnalysisUseCase                    │
                    │  1. GitHubURL 파싱                                     │
                    │  2. Repository 메타데이터 조회                          │
                    │  3. 파일 트리 조회                                     │
                    │  4. 핵심 소스 파일 조회                                 │
                    │  5. RepositoryAnalysis 엔티티 생성                    │
                    └──────────────────────────────┬────────────────────────┘
                                                   │
        ┌───────────────────────────────────────────┼───────────────────────────────┐
        │                                           │                               │
        ▼                                           ▼                               ▼
┌───────────────┐                     ┌──────────────────┐               ┌─────────────────┐
│   GitHub      │                     │  MultiDocument   │               │    Diagram      │
│  Repository   │                     │    Analyzer      │               │   Renderer      │
│ (Adapter)     │                     │  (AI Analysis)   │               │  (Mermaid)      │
└───────┬───────┘                     └────────┬─────────┘               └─────────────────┘
        │                                       │                                                 
        │  fetch_metadata()                     │  analyze_multidoc()                              
        │  fetch_file_tree()                   │  - project_summary                              
        │  fetch_source_files()                │  - api_spec                                     
        │                                       │  - erd, sequence, architecture                  
        └───────────────────────────────────────┘  - dependencies, structure, state_machine    
                                                   │                                                 
                                                   ▼                                                 
                    ┌──────────────────────────────────────────────────────┐
                    │           ZIPPackagingService                       │
                    │  - 7개 Markdown 파일을 ZIP으로 압축                 │
                    └───────────────────────────────┬────────────────────┘
                                                   │
                    ┌───────────────────────────────▼─────────────────────┐
                    │           AzureBlobStorageService                   │
                    │  - ZIP 파일 업로드                                  │
                    │  - SAS URL 생성 (24시간 유효)                      │
                    └───────────────────────────────┬────────────────────┘
                                                   │
                    ┌───────────────────────────────▼─────────────────────┐
                    │            TeamsCardBuilder                          │
                    │  - 프로젝트 요약 + 다운로드 버튼 (Adaptive Card)    │
                    └───────────────────────────────┬────────────────────┘
                                                   │
                                                   ▼
                    ┌──────────────────────────────────────────────────────┐
                    │               Teams Bot Service                      │
                    │              (응답 메시지 전송)                       │
                    └──────────────────────────────────────────────────────┘
```

### 4.2 상세 동작 단계

#### Step 1: 사용자 입력
```
Teams에서 "@Spec Bot https://github.com/owner/repo" 입력
```

#### Step 2: Azure Functions 트리거
```
function_app.py → messages HTTP Trigger
```

#### Step 3: HTTP Handler 처리 (http_handler.py)
1. Teams Activity 파싱
2. 도움말 명령어 확인
3. GitHub URL 추출 (정규식)
4. 입력 검증 (Pydantic)
5. ACK 메시지 생성

#### Step 4: Use Case 실행 (MultiDocumentAnalysisUseCase)

**Step 4-1: Repository 데이터 수집**
- `GitHubURL` 값 객체 생성
- `github_repository.fetch_metadata()` - 메타데이터 조회
- `github_repository.fetch_file_tree()` - 파일 트리 조회
- `github_repository.fetch_source_files()` - 핵심 소스 파일 조회
- `RepositoryAnalysis` 엔티티 생성

**Step 4-2: AI 분석**
- `MultiDocumentAnalyzer.analyze_multidoc()` 호출
- Azure OpenAI (kimi-k2.5)에게 7개 문서 생성 요청
- System Prompt로 Mermaid 문법 강제

**Step 4-3: ZIP 패키징**
- 7개 Markdown 파일 생성:
  - `api_spec.md`
  - `erd.md`
  - `sequence.md`
  - `architecture.md`
  - `dependencies.md`
  - `structure.md`
  - `state_machine.md`
- `ZIPPackagingService.create_zip()` - 메모리 내 ZIP 압축

**Step 4-4: Blob Storage 업로드**
- `AzureBlobStorageService.upload_zip()` - ZIP 파일 업로드
- SAS 토큰 생성 (24시간 유효)

**Step 4-5: Adaptive Card 생성**
- `TeamsCardBuilder.build_download_card()` - 다운로드 버튼 포함 카드 생성

#### Step 5: Teams 응답
```
Adaptive Card (프로젝트 요약 + 다운로드 버튼) 전송
```

---

## 5. 핵심 컴포넌트

### 5.1 도메인 레이어

#### Entities (src/domain/entities/repository.py)
| Entity | 설명 |
|--------|------|
| `SourceFile` | 소스 파일 (path, content, FileType) |
| `RepositoryMetadata` | 레포지토리 메타데이터 (owner, name, language, description) |
| `RepositoryAnalysis` | 분석 결과 Aggregate Root |
| `ProjectSummary` | 프로젝트 요약 값 객체 |
| `APIEndpoint` | API 엔드포인트 값 객체 |

#### Value Objects (src/domain/value_objects/github.py)
| Value Object | 설명 |
|--------------|------|
| `GitHubURL` | GitHub URL 값 객체 (검증 로직 포함) |
| `FilePath` | 파일 경로 값 객체 |
| `SourceCode` | 소스 코드 값 객체 |

#### Interfaces (Ports) (src/domain/interfaces/repositories.py)
| Interface | 설명 |
|-----------|------|
| `GitHubRepository` | GitHub 데이터 조회 포트 |
| `AIAnalyzer` | AI 분석 포트 |
| `DiagramRenderer` | 다이어그램 렌더링 포트 |
| `CardBuilder` | Adaptive Card 빌더 포트 |

### 5.2 애플리케이션 레이어

#### DTOs (src/application/dto/multidoc.py)
| DTO | 설명 |
|-----|------|
| `MultiDocumentAnalysisInput` | 입력 DTO (github_url 검증) |
| `MultiDocumentAnalysisOutput` | 출력 DTO (zip_blob_url, summary, document_count) |

#### Use Cases (src/application/use_cases/multi_doc_analysis.py)
| Use Case | 설명 |
|----------|------|
| `MultiDocumentAnalysisUseCase` | 7개 문서 분석 및 ZIP 생성 유스 케이스 |

### 5.3 인프라스트럭처 레이어

#### Adapters (src/infrastructure/)
| Adapter | 설명 |
|---------|------|
| `PyGitHubRepository` | GitHub API Adapter (PyGithub) |
| `AzureOpenAIService` | Azure OpenAI Adapter |
| `MultiDocumentAnalyzer` | 7문서 AI 분석기 |
| `MermaidInkRenderer` | Mermaid 이미지 렌더러 |
| `TeamsCardBuilder` | Teams Adaptive Card 빌더 |
| `AzureBlobStorageService` | Azure Blob Storage Adapter |
| `ZIPPackagingService` | ZIP 파일 패키저 |
| `TeamsBotService` | Teams Bot 메시지 서비스 |

---

## 6. 환경 설정

### 필수 환경 변수

```bash
# Azure Bot Configuration
AZURE_BOT_ID=your_bot_app_id
AZURE_BOT_PASSWORD=your_bot_password

# Azure OpenAI Configuration
OPENAI_API_KEY=your_azure_openai_api_key
OPENAI_API_ENDPOINT=https://your-resource-name.openai.azure.com/
OPENAI_API_VERSION=2024-02-15-preview
OPENAI_DEPLOYMENT_NAME=kimi-k2.5

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...

# GitHub (optional - public repos don't need token)
GITHUB_TOKEN=your_github_pat
```

---

## 7. 생성되는 문서

| 파일 | 설명 | Mermaid 포함 |
|------|------|-------------|
| `api_spec.md` | OpenAPI 3.0 규격 API 명세 | - |
| `erd.md` | 엔티티 관계 다이어그램 | erDiagram |
| `sequence.md` | 비즈니스 로직 플로우 | sequenceDiagram |
| `architecture.md` | 계층/모듈 구조 | flowchart |
| `dependencies.md` | 빌드 도구, 외부 서비스, 라이브러리 | - |
| `structure.md` | 디렉토리 트리 + AI 주석 | - |
| `state_machine.md` | 도메인 상태 전이도 | stateDiagram-v2 |

---

## 8. Azure 배포 아키텍처

```
┌─────────────────┐
│   Microsoft     │
│    Teams        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Azure Bot      │
│   Service       │
└────────┬────────┘
         │ (HTTPS Webhook)
         ▼
┌─────────────────┐     ┌──────────────────┐
│    Azure        │────▶│    Azure         │
│  Functions      │     │  Blob Storage    │
│  (Python)       │     │  (ZIP files)     │
└─────────────────┘     └──────────────────┘
         │
         ▼
┌─────────────────┐
│   Azure         │
│   OpenAI        │
│ (kimi-k2.5)     │
└─────────────────┘
```

---

## 9. 테스트 전략

테스트는 TDD(테스트 주도 개발) 방식으로 구성됩니다:

```
tests/
└── unit/
    ├── domain/           # 도메인 엔티티 및 값 객체 테스트
    │   └── test_repository.py
    ├── application/      # Use Case 및 DTO 테스트
    │   └── test_multi_doc_analysis.py
    └── infrastructure/   # Adapter 테스트
        ├── test_github.py
        └── test_blob_storage.py
```

### 테스트 실행
```bash
pytest tests/ -v
pytest tests/unit/domain/ -v
pytest tests/unit/application/ -v
pytest tests/unit/infrastructure/ -v
```

### 타입 검사
```bash
mypy src/
mypy src/ --strict
```

---

## 10. 보안 고려사항

1. **SAS URL 만료**: 24시간 후 자동 만 **Blob Lifecycle**:료
2. 불필요한 파일 자동 삭제 정책 적용
3. **소스 코드 미저장**: 분석 후 소스 코드 외부 저장소 미보관
4. **Private Repo**: GitHub PAT 사용 시 보안 채널 통해 입력
