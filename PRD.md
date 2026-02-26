# [PRD] Spec Bot: AI 기반 기술 문서 자동화 Teams 에이전트

## 1. 프로젝트 개요

- **프로젝트 명:** Spec Bot
- **목적:** 사용자가 Microsoft Teams 채팅으로 GitHub 레포지토리 URL을 입력하면, AI가 소스 코드를 분석하여 핵심 기술 문서(API Spec, ERD, Sequence, Architecture 등 7종)를 자동 생성하고, 이를 `.zip` 파일로 묶어 다운로드 링크와 함께 응답하는 봇.
- **제약 사항:** Copilot Studio를 사용하지 않고, 순수 Azure 리소스(Azure Bot Service, Azure Functions, Azure Blob Storage)만을 활용하여 커스텀 봇으로 구현.
- **핵심 가치:**
  - **생산성:** 수동 문서화 작업 및 레거시 코드 파악 시간 90% 단축.
  - **정확성:** 최신 소스 코드 기반의 아키텍처, 스펙, 도메인 상태 파악.
  - **편의성:** 채팅창을 도배하지 않고, 깔끔한 요약본과 통합 압축 파일(.zip) 다운로드 제공.

## 2. 시스템 아키텍처 및 기술 스택

### 2.1 기술 스택

- **Interface:** Microsoft Teams
- **Bot Framework:** Azure Bot Service (App Type: Single Tenant, Create new Microsoft App ID)
- **Backend:** Azure Functions (Python 3.11+, HTTP Trigger)
- **Storage:** Azure Blob Storage (결과물 압축 파일 저장 및 일회성 SAS URL 발급용)
- **Data Validation:** Pydantic (요청 파라미터 및 OpenAI 구조화된 출력 검증용)
- **Type Safety**: mypy (strict mode)
- **AI Engine:** Azure OpenAI Service (kimi-k2.5)
- **API 연동:** GitHub REST API (PyGithub 라이브러리 활용)
- **Diagram Rendering:** Mermaid.js 문법 생성 (Markdown 내장 및 필요시 이미지 변환)

## 3. 기능 요구사항 (Functional Requirements)

### 3.1 GitHub 레포지토리 수집 및 지능형 필터링

- **URL 인식:** Teams 메시지에서 GitHub URL 추출 및 유효성 검증.
- **지능형 스캐닝 (확장):** 전체 코드가 아닌, 아키텍처와 비즈니스 로직을 결정짓는 핵심 파일 선별 추출.
  - **로직/도메인:** `Controller`, `Service`, `Entity`, `Domain`, `Enum` (상태값) 등.
  - **설정/인프라:** `pom.xml`, `build.gradle`, `requirements.txt`, `docker-compose.yml`, `application.yml` 등 의존성 및 환경 설정 파일.
- **Private Repo 지원 (Phase 3):** 사용자로부터 GitHub PAT(Personal Access Token)를 안전하게 입력받아 접근 권한 확보.

### 3.2 문서 자동 생성 및 파일 패키징 (Core Logic)

AI(Azure OpenAI)가 추출된 코드와 설정 파일을 분석하여 아래 **7가지 핵심 문서**를 생성합니다.

1. **API Specification (`api_spec.md`):** 라우터/컨트롤러 코드를 바탕으로 OpenAPI 3.0 규격에 준하는 문서 생성.
2. **ERD (`erd.md`):** Entity/Model 코드를 분석하여 데이터베이스 관계 추론. (Mermaid `erDiagram` 포함)
3. **Sequence Diagram (`sequence.md`):** Service 계층의 주요 비즈니스 로직 플로우 시각화. (Mermaid `sequenceDiagram` 포함)
4. **Architecture Diagram (`architecture.md`):** 폴더 구조와 의존성 주입(DI) 내역을 분석하여 계층(Layer) 간 통신 및 모듈 구조 시각화. (Mermaid `flowchart` 포함)
5. **Setup & Dependencies (`dependencies.md`):** 빌드/설정 파일을 분석하여 프로젝트 실행 환경, 외부 인프라(DB, Redis, Kafka 등), 주요 라이브러리 요약.
6. **Annotated Project Structure (`structure.md`):** 프로젝트의 주요 디렉토리 트리를 구성하고, 각 폴더가 담당하는 역할(예: 비즈니스 로직, 인프라 연동 등)에 대해 AI 주석 추가.
7. **State Diagram (`state_machine.md`):** 복잡한 도메인 생명주기(예: 결제, 주문, 승인 상태)를 가진 Enum이나 Service 로직을 분석하여 상태 전이도 시각화. (Mermaid `stateDiagram` 포함)

- **파일 압축 (.zip):** 생성된 7개의 마크다운 파일을 메모리(런타임) 상에서 하나의 `.zip` 파일로 압축.
- **Storage 업로드:** 완성된 `.zip` 파일을 Azure Blob Storage에 업로드하고, 24시간 유효한 SAS(Shared Access Signature) URL 발급.

### 3.3 비동기 알림 시스템 및 Teams UX

- **상태 알림 (ACK):** 분석 요청 즉시 "프로젝트 분석을 시작합니다. 다수의 문서를 생성하므로 약 1~2분 소요될 수 있습니다." 메시지 응답.
- **결과 전송 (Adaptive Card):**
  - 프로젝트 핵심 요약 (사용 기술 스택, 프로젝트 목적) 간략히 표기.
  - 발급된 SAS URL을 연결한 **[📦 기술 문서 패키지 다운로드 (.zip)]** 버튼(`Action.OpenUrl`) 포함.

## 4. 사용자 시나리오 및 Data Flow

1. **Input:** 사용자가 Teams 채널에서 `@Spec Bot https://github.com/user/repo` 입력.
2. **Validate & ACK:** Azure Function이 URL 검증 후 "분석 중" 텍스트를 Teams에 즉시 반환.
3. **Collect:** GitHub API를 통해 파일 트리 조회 후 코드 스니펫 및 **설정/빌드 파일** 메모리 적재.
4. **Infer:** 수집된 데이터를 Pydantic 스키마(7개 문서 구조)와 함께 Azure OpenAI에 전달하여 다각도 분석 및 문서 데이터 추출.
5. **Package:** 추출된 데이터를 7개의 `.md` 파일로 구성하고 메모리 내장 `zipfile` 모듈을 사용해 `.zip` 압축.
6. **Upload:** Azure Blob Storage에 `.zip` 파일 업로드 후 다운로드용 SAS URL 생성.
7. **Output:** 프로젝트 요약과 다운로드 버튼이 포함된 간결한 Adaptive Card를 구성하여 Teams Bot API를 통해 전송.

## 5. 상세 기능 리스트 및 Vibe Coding Task (우선순위 순)

AI 에이전트에게 코드를 지시할 때 아래 Task 단위로 나누어 지시하세요.

- **Task 1: Azure Function, Bot Framework & Blob Storage 셋업**
  - Python Azure Function (HTTP Trigger) 뼈대 및 Teams 메시지 핸들러 구현.
  - Azure Blob Storage 연결 및 파일 업로드, SAS URL 생성 유틸리티 함수 구현.
- **Task 2: GitHub Repository Scraper 구현 (고도화)**
  - 정규식을 활용하여 소스 코드뿐만 아니라 `pom.xml`, `requirements.txt` 등 빌드/설정 파일까지 포함하는 필터링 및 텍스트 추출 모듈 구현.
- **Task 3: Azure OpenAI 연동 및 다중 문서 Pydantic 파싱**
  - 시스템 프롬프트 작성 및 Pydantic을 활용하여 7가지 문서를 한 번에(또는 병렬로) 객체화하여 응답받는 로직 구현. (Mermaid 문법 엄수 지시 포함)
- **Task 4: Zip 패키징 및 Adaptive Card 빌더**
  - AI 응답 데이터를 7개의 `.md` 파일들로 나누어 `.zip`으로 메모리 압축하는 로직 구현.
  - 요약 정보와 SAS 다운로드 버튼이 포함된 Adaptive Card JSON 템플릿 작성 및 전송 로직 구현.

## 6. 비기능 요구사항 (Non-Functional)

- **보안:** 생성된 `.zip` 파일은 Blob Storage에 저장되나, SAS URL 만료 기간(24시간) 설정 및 Blob Lifecycle Management를 통해 자동 삭제되도록 구성. 소스 코드는 외부 DB에 저장하지 않음.
- **성능:** 다수의 문서 생성을 위해 OpenAI API 호출 시 병렬 처리(Asyncio)를 고려하거나, Azure Durable Functions를 도입하여 Teams의 응답 시간 초과(Timeout) 방지.

## 7. 로드맵 (Roadmap)

- **Phase 1:** 기본 Teams 봇 생성, GitHub 스캐닝, 7종 마크다운 문서 생성 및 Zip 파일 Blob Storage 다운로드 연동.
- **Phase 2:** Mermaid 코드를 `mermaid.ink` 등을 통해 실제 이미지 파일(.png)로 렌더링하여 Zip 파일에 추가 포함.
- **Phase 3:** 처리 안정성을 위한 Azure Durable Functions 완벽 도입 및 Private Repo 접근(PAT) 보안 연동.
