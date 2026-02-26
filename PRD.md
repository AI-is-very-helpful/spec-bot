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
- **메모리 기반 Zipball 처리 (성능 최적화):** GitHub REST API의 Zipball 기능을 호출하여 바이트 스트림으로 레포지토리를 다운로드하고, `io.BytesIO`와 `zipfile`을 활용해 디스크 I/O 없이 메모리 상에서 파일 압축을 해제 및 스캐닝.
- **지능형 스캐닝 및 산출물 맞춤형 파일 라우팅 (핵심):** 전체 코드가 아닌 핵심 파일(최대 30개, 각 5000자 제한)을 선별한 뒤, **백엔드에서 분석하여 각 산출물(7종) 생성에 필요한 파일들만 개별적으로 분류하여 LLM에 전달**합니다.
  - _예시:_ API 스펙에는 `Controller`, `DTO`, `Router` 위주 전달 / ERD에는 `Entity`, `Model`, `Schema` 위주 전달 / Dependencies에는 `pom.xml`, `build.gradle` 위주 전달.
- **Private Repo 지원 (Phase 3):** 사용자로부터 GitHub PAT(Personal Access Token)를 안전하게 입력받아 접근 권한 확보.

### 3.2 문서 자동 생성 및 파일 패키징 (Core Logic)

AI(Azure OpenAI)가 추출 및 분류된 코드를 바탕으로 아래 **7가지 핵심 문서**를 **비동기 병렬(Parallel)**로 동시 생성합니다.

1. **API Specification (`api_spec.md`):** 라우터/컨트롤러/DTO 코드를 바탕으로 OpenAPI 3.0 규격에 준하는 문서 생성. **(반드시 Request Body, Response Body, Header, Path/Query Parameters 등 API를 실제 활용하기 위한 모든 상세 정보를 포함해야 함)**
2. **ERD (`erd.md`):** Entity/Model 코드를 분석하여 데이터베이스 관계 추론. (Mermaid `erDiagram` 포함)
3. **Sequence Diagram (`sequence.md`):** Service 계층의 주요 비즈니스 로직 플로우 시각화. (Mermaid `sequenceDiagram` 포함)
4. **Architecture Diagram (`architecture.md`):** 폴더 구조와 의존성 주입(DI) 내역을 분석하여 계층(Layer) 간 통신 및 모듈 구조 시각화. (Mermaid `flowchart` 포함)
5. **Setup & Dependencies (`dependencies.md`):** 빌드/설정 파일을 분석하여 프로젝트 실행 환경, 외부 인프라(DB, Redis, Kafka 등), 주요 라이브러리 요약.
6. **Annotated Project Structure (`structure.md`):** 프로젝트의 주요 디렉토리 트리를 구성하고, 각 폴더가 담당하는 역할(예: 비즈니스 로직, 인프라 연동 등)에 대해 AI 주석 추가.
7. **State Diagram (`state_machine.md`):** 복잡한 도메인 생명주기(예: 결제, 주문, 승인 상태)를 가진 Enum이나 Service 로직을 분석하여 상태 전이도 시각화. (Mermaid `stateDiagram` 포함)

- **병렬 처리 및 동기화:** 7개의 산출물 생성 요청은 동시에 실행되며, **모든 LLM 응답 결과가 도착할 때까지 대기(Wait)**합니다.
- **파일 압축 (.zip):** 모든 결과가 모이면, 7개의 마크다운 파일을 메모리(런타임) 상에서 하나의 `.zip` 파일로 압축.
- **Storage 업로드:** 완성된 `.zip` 파일을 Azure Blob Storage에 업로드하고, 24시간 유효한 SAS(Shared Access Signature) URL 발급.

### 3.3 비동기 알림 시스템 및 Teams UX

- **상태 알림 (ACK):** 분석 요청 즉시 "프로젝트 분석을 시작합니다. 다수의 문서를 생성하므로 약 1~2분 소요될 수 있습니다." 메시지 응답.
- **결과 전송 (Adaptive Card):**
  - 프로젝트 핵심 요약 (사용 기술 스택, 프로젝트 목적) 간략히 표기.
  - 발급된 SAS URL을 연결한 **[📦 기술 문서 패키지 다운로드 (.zip)]** 버튼(`Action.OpenUrl`) 포함.

## 4. 사용자 시나리오 및 Data Flow

1. **Input:** 사용자가 Teams 채널에서 `@Spec Bot https://github.com/user/repo` 입력.
2. **Validate & ACK:** Azure Function이 URL 검증 후 "분석 중" 텍스트를 Teams에 즉시 반환.
3. **Collect & Route:** GitHub REST API를 통해 Zipball을 바이트 스트림으로 요청 및 메모리에서 압축 해제. 정규식으로 핵심 파일(30개 이하)을 추출한 뒤, **백엔드 로직을 통해 7개의 산출물 각각에 필요한 메타데이터, 파일 트리, 맞춤형 소스 파일 묶음으로 라우팅/분류**합니다.
4. **Infer (Parallel):** 분류된 데이터를 Pydantic 스키마와 함께 Azure OpenAI로 전달합니다. 이때 **7개의 산출물 요청을 비동기(Asyncio)로 동시에 호출하고, 모든 응답이 완료될 때까지 기다립니다(Gather).**
5. **Package:** 완료된 7개의 `.md` 결과물을 모아 메모리 내장 `zipfile` 모듈을 사용해 `.zip` 압축.
6. **Upload:** Azure Blob Storage에 `.zip` 파일 업로드 후 다운로드용 SAS URL 생성.
7. **Output:** 프로젝트 요약과 다운로드 버튼이 포함된 간결한 Adaptive Card를 구성하여 Teams Bot API를 통해 전송.

## 5. 상세 기능 리스트 및 Vibe Coding Task (우선순위 순)

AI 에이전트에게 코드를 지시할 때 아래 Task 단위로 나누어 지시하세요.

- **Task 1: Azure Function, Bot Framework & Blob Storage 셋업**
  - Python Azure Function (HTTP Trigger) 뼈대 및 Teams 메시지 핸들러 구현.
  - Azure Blob Storage 연결 및 파일 업로드, SAS URL 생성 유틸리티 함수 구현.
- **Task 2: GitHub Zipball Scraper & Artifact Router 구현**
  - Zipball 바이트 스트림 다운로드 및 `io.BytesIO` 메모리 압축 해제 로직 구현.
  - 핵심 파일 추출 후, 7개 산출물(API, ERD, Sequence 등) 각각의 목적에 맞게 필요한 소스 코드만 매핑/필터링하여 전달하는 라우터 클래스 구현.
- **Task 3: Azure OpenAI 병렬 연동 및 Pydantic 파싱 (핵심 로직)**
  - 산출물별 특화된 시스템 프롬프트 작성 (특히 API 스펙 문서에는 Request/Response Body 등 모든 상세 정보 필수 포함 지시).
  - `asyncio.gather` 등을 활용하여 7개의 문서를 비동기 병렬로 동시 요청하고, 모든 결과를 기다렸다가 취합하는 로직 구현.
- **Task 4: Zip 패키징 및 Adaptive Card 빌더**
  - 병렬 처리로 수집된 7개의 `.md` 데이터를 `.zip`으로 메모리 압축.
  - 요약 정보와 SAS 다운로드 버튼이 포함된 Adaptive Card JSON 템플릿 작성 및 전송 로직 구현.

## 6. 비기능 요구사항 (Non-Functional)

- **성능 (병렬 처리 필수):** 다수의 문서 생성을 순차적으로 진행할 경우 타임아웃이 발생하므로, 반드시 비동기 병렬 처리(`asyncio`)를 적용하여 전체 소요 시간을 획기적으로 단축. Zipball 메모리 처리를 통해 API Rate Limit 보호 및 디스크 I/O 병목 방지.
- **보안:** 생성된 `.zip` 파일은 Blob Storage에 저장되나, SAS URL 만료 기간(24시간) 설정 및 Blob Lifecycle Management를 통해 자동 삭제되도록 구성. 레포지토리 원본 소스 코드는 외부 스토리지나 디스크에 절대 저장하지 않고 순수 메모리 상에서만 처리됨.

## 7. 로드맵 (Roadmap)

- **Phase 1:** 기본 Teams 봇 생성, GitHub 스캐닝, 7종 마크다운 문서 병렬 생성 및 Zip 파일 Blob Storage 다운로드 연동.
- **Phase 2:** Mermaid 코드를 `mermaid.ink` 등을 통해 실제 이미지 파일(.png)로 렌더링하여 Zip 파일에 추가 포함.
- **Phase 3:** 처리 안정성을 위한 Azure Durable Functions 완벽 도입 및 Private Repo 접근(PAT) 보안 연동.
