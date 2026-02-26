# Spec Bot

Microsoft Teams에서 GitHub 레포지토리 URL을 입력하면 AI가 자동으로 **7가지 핵심 기술 문서**를 생성하고, `.zip` 파일로 다운로드 가능한 Teams 에이전트.

## 주요 기능

- **7가지 기술 문서 자동 생성**:
  1. **API Specification**: OpenAPI 3.0 규격 Markdown 문서
  2. **ERD**: Mermaid erDiagram 기반 엔티티 관계
  3. **Sequence Diagram**: 비즈니스 로직 플로우 시각화
  4. **Architecture Diagram**: 계층/모듈 구조 (Mermaid flowchart)
  5. **Setup & Dependencies**: 빌드 도구, 외부 서비스, 라이브러리
  6. **Project Structure**: 디렉토리 트리 + AI 주석
  7. **State Machine**: 도메인 생명주기 (Mermaid stateDiagram)

- **ZIP 패키징**: 7개 문서를 하나의 `.zip` 파일로 압축
- **Azure Blob Storage**: ZIP 파일 업로드 및 24시간 유효 SAS URL 발급
- **Adaptive Card**: 프로젝트 요약 + 다운로드 버튼

## 기술 스택

- **Backend**: Azure Functions (Python 3.11+)
- **Storage**: Azure Blob Storage (ZIP 저장 + SAS URL)
- **AI**: Azure OpenAI Service (kimi-k2.5)
- **Bot**: Microsoft Teams Bot Framework
- **Architecture**: Clean Architecture + Hexagonal Architecture
- **Validation**: Pydantic
- **Type Safety**: mypy (strict mode)

## 프로젝트 구조 (Clean Architecture)

```
spec-bot/
├── src/
│   ├── domain/                          # 도메인 레이어 (핵심 비즈니스 로직)
│   │   ├── entities/                    # 엔티티
│   │   │   └── repository.py            # SourceFile, RepositoryAnalysis
│   │   ├── value_objects/              # 값 객체
│   │   │   └── github.py               # GitHubURL, FilePath, SourceCode
│   │   ├── interfaces/                  # 포트 (인터페이스)
│   │   │   └── repositories.py         # GitHubRepository, AIAnalyzer
│   │   └── __init__.py
│   │
│   ├── application/                      # 애플리케이션 레이어 (유스 케이스)
│   │   ├── dto/                         # Data Transfer Objects
│   │   │   ├── repository.py            # 단일 문서 DTO
│   │   │   └── multidoc.py              # 7문서 DTO
│   │   ├── use_cases/                   # 유스 케이스
│   │   │   ├── analyze_repository.py   # 단일 문서 UseCase
│   │   │   └── multi_doc_analysis.py   # 7문서 UseCase
│   │   └── __init__.py
│   │
│   ├── infrastructure/                   # 인프라스트럭처 레이어 (외부 연동)
│   │   ├── repositories/                # 레포지토리 구현
│   │   │   └── github.py               # PyGitHubRepository
│   │   ├── services/                   # 외부 서비스 구현
│   │   │   ├── openai.py               # AzureOpenAIService
│   │   │   ├── multi_doc_analyzer.py   # 7문서 AI 분석
│   │   │   ├── mermaid.py              # MermaidInkRenderer
│   │   │   ├── card.py                 # TeamsCardBuilder
│   │   │   ├── blob_storage.py         # Azure Blob Storage
│   │   │   ├── zip_packager.py         # ZIP 패키징
│   │   │   ├── teams_bot.py            # Teams Bot Service
│   │   │   └── logging_config.py       # 로깅 설정
│   │   └── __init__.py
│   │
│   └── presentation/                    # 프레젠테이션 레이어 (API)
│       └── handlers/
│           └── http_handler.py          # Azure Functions HTTP Trigger
│
├── tests/                               # 테스트 (TDD - 84개)
│   └── unit/
│       ├── domain/                      # 도메인 테스트
│       ├── application/                  # 애플리케이션 테스트
│       └── infrastructure/              # 인프라스트럭처 테스트
│
├── mypy.ini                             # mypy 타입 검사 설정
├── pytest.ini                           # pytest 설정
├── host.json                            # Azure Functions 설정
├── requirements.txt                     # Python 의존성
├── .env.example                         # 환경변수 예시
├── run.sh                               # 로컬 실행 스크립트
├── run.ps1                              # 로컬 실행 스크립트 (Windows)
└── PRD.md                               # 프로젝트 요구사항
```

## 의존성 설치

### 시스템 Python (Azure Functions용)

Azure Functions Core Tools는 시스템 Python을 사용합니다:

```bash
# 의존성 설치 (시스템 Python)
pip install --break-system-packages -r requirements.txt
```

### 가상환경 (개발 도구용)

테스트 및 타입 검증을 위한 가상환경:

```bash
# 가상환경 생성
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 개발 의존성 설치
pip install pytest pytest-mock pytest-cov mypy
```

## 환경 설정

1. `.env.example`을 `.env`로 복사:

```bash
cp .env.example .env
```

2. `.env` 파일 편집:

```bash
# Azure Bot Configuration
AZURE_BOT_ID=your_bot_app_id
AZURE_BOT_PASSWORD=your_bot_app_password

# Azure OpenAI Configuration
OPENAI_API_KEY=your_azure_openai_api_key
OPENAI_API_ENDPOINT=https://your-resource-name.openai.azure.com/
OPENAI_API_VERSION=2024-02-15-preview
OPENAI_DEPLOYMENT_NAME=kimi-k2.5

# Azure Blob Storage Configuration
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your_account;AccountKey=your_key==

# GitHub (optional - public repos don't need token)
# GITHUB_TOKEN=your_github_pat
```

## 로컬 실행

```bash
# 스크립트 사용 (권장)
./run.sh

# 또는 직접 실행
func start
```

## 테스트 실행 (TDD)

```bash
# 가상환경 활성화 (개발 도구용)
source .venv/bin/activate

# 모든 테스트 실행
pytest tests/ -v

# 커버리지 포함
pytest tests/ --cov=src --cov-report=html

# 특정 레이어 테스트만
pytest tests/unit/domain/ -v
pytest tests/unit/application/ -v
pytest tests/unit/infrastructure/ -v
```

## 타입 검사

```bash
# mypy 타입 검사
mypy src/

# 엄격 모드
mypy src/ --strict
```

## Azure 배포

### Step 1. Azure CLI 로그인 및 기본 환경 준비

```bash
# Azure 로그인
az login

# (선택) 기본 리소스 그룹 지정
az config set defaults.group=<your-rg>
```

### Step 2. Azure Storage Account 및 Blob 컨테이너 생성

```bash
# 1. 스토리지 계정 생성
az storage account create \
  --name <your-storage> \
  --resource-group <your-rg> \
  --location koreacentral \
  --sku Standard_LRS

# 2. 스토리지 연결 문자열 추출
az storage account show-connection-string \
  --name <your-storage> \
  --resource-group <your-rg> \
  --query connectionString \
  --output tsv

# 3. Blob 컨테이너 생성
az storage container create \
  --name spec-bot-documents \
  --public-access off \
  --connection-string "<연결 문자열>"
```

### Step 3. Azure Function App 생성

```bash
az functionapp create \
  --resource-group <your-rg> \
  --name <your-spec-bot> \
  --storage-account <your-storage> \
  --consumption-plan-location koreacentral \
  --runtime python \
  --runtime-version 3.11 \
  --os-type linux
```

### Step 4. 환경 변수 (App Settings) Azure에 등록

```bash
az functionapp config appsettings set \
  --name <your-spec-bot> \
  --resource-group <your-rg> \
  --settings \
  AZURE_BOT_ID="<your_bot_id>" \
  AZURE_BOT_PASSWORD="<your_bot_password>" \
  AZURE_STORAGE_CONNECTION_STRING="<스토리지 연결 문자열>" \
  OPENAI_API_KEY="<OpenAI API 키>" \
  OPENAI_BASE_URL="<Azure OpenAI 엔드포인트>" \
  OPENAI_DEPLOYMENT_NAME="kimi-k2.5"
```

### Step 5. Azure에 배포

```bash
func azure functionapp publish <your-spec-bot>
```

### Step 6. Azure Bot Service 엔드포인트 연결

1. Azure Portal → Azure Bot 리소스 → Configuration
2. Messaging endpoint: `https://<your-spec-bot>.azurewebsites.net/api/messages`
3. Apply 클릭

### Step 7. Teams 채널 연동

1. Azure Bot 리소스 → Channels
2. Microsoft Teams 추가
3. 서비스 약관 동의 후 Save
4. "Open in Teams" 클릭

## 사용법

Teams에서 다음과 같이 입력:

```
@Spec Bot https://github.com/owner/repo
```

응답:

- 분석 시작 ACK 메시지
- 7개 문서가 ZIP으로 압축되어 Azure Blob Storage에 업로드
- SAS URL이 포함된 Adaptive Card 수신
- **[📦 기술 문서 패키지 다운로드 (.zip)]** 버튼 클릭

## 생성되는 문서

| 파일               | 설명                                    |
| ------------------ | --------------------------------------- |
| `api_spec.md`      | OpenAPI 3.0 규격 API 명세               |
| `erd.md`           | Mermaid erDiagram 엔티티 관계           |
| `sequence.md`      | Mermaid sequenceDiagram 비즈니스 플로우 |
| `architecture.md`  | Mermaid flowchart 아키텍처              |
| `dependencies.md`  | 빌드 도구, 외부 서비스, 라이브러리      |
| `structure.md`     | 디렉토리 트리 + AI 주석                 |
| `state_machine.md` | Mermaid stateDiagram 도메인 상태        |

## Clean Architecture 원칙

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation Layer                     │
│              (HTTP Handlers, Controllers)                │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                    Application Layer                      │
│                  (Use Cases, DTOs)                      │
└─────────────────────────┬───────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                      Domain Layer                         │
│           (Entities, Value Objects, Interfaces)          │
└─────────────────────────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────┐
│                   Infrastructure Layer                    │
│    (GitHub API, OpenAI, Blob Storage, ZIP, Teams)       │
└─────────────────────────────────────────────────────────┘
```

## 라이선스

MIT
