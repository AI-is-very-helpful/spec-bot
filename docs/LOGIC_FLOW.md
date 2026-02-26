# Spec Bot — 로직 흐름 (상세)

이 문서는 **요청이 들어온 순간부터 응답이 나갈 때까지** 코드가 어떻게 흐르는지 단계별로 적어 둔 것이다.

---

## 1. 진입점과 실행 경로

```
로컬: run.sh / run.ps1  →  func start  →  Azure Functions 호스트가 function_app.py 로드
Azure: 배포 시 호스트가 function_app.py 로드

function_app.py
  └─ @app.route(route="messages", methods=["POST"])
  └─ messages(req)  →  http_handler_main(req)  (src/presentation/handlers/http_handler.py)
```

- **실제 진입점**: `function_app.py`의 `messages()` 함수.
- **핸들러**: `src/presentation/handlers/http_handler.py`의 `main()` (이름만 `http_handler_main`으로 import됨).
- **로컬 실행**: `run.sh`(Mac/Linux) 또는 `run.ps1`(Windows)는 venv 활성화 후 `func start`만 실행하는 래퍼다. 로직은 동일하게 `function_app.py` → `http_handler.main`으로 진입한다.

---

## 2. HTTP 요청 → 응답까지 (전체 흐름)

### 2.1 요청 수신 ~ 메시지 판별

| 단계 | 파일 | 처리 내용 |
|------|------|-----------|
| 1 | `http_handler.main(req)` | `req.get_json()`으로 Body 파싱. 실패 시 `{}`. |
| 2 | `TeamsBotService.parse_teams_activity(req_body)` | `type == "message"` 인지 확인. 아니면 `None` 반환. |
| 3 | activity가 `None` | `{"status": "OK"}` 200 반환 후 종료. (Teams가 보내는 일부 이벤트는 무시) |
| 4 | `activity.get("text", "")` | 사용자가 보낸 메시지 문자열 추출. |

### 2.2 도움말 / GitHub URL 추출

| 단계 | 파일 | 처리 내용 |
|------|------|-----------|
| 5 | `TeamsBotService.is_help_command(message)` | "help", "/help", "도움말" 등이면 True. |
| 6 | 도움말이면 | `MessageFactory.create_help_message()` JSON으로 200 반환 후 종료. |
| 7 | `TeamsBotService.extract_github_url(message)` | 정규식으로 `https://github.com/owner/repo` 형태 추출. |
| 8 | URL 없으면 | `MessageFactory.create_github_not_found_message()` 200 반환 후 종료. |

### 2.3 입력 검증 ~ 유스케이스 실행

| 단계 | 파일 | 처리 내용 |
|------|------|-----------|
| 9 | `MultiDocumentAnalysisInput(github_url=repo_url)` | Pydantic 검증 (빈 값, github.com 포함 여부). 실패 시 `MessageFactory.create_error_message()` 200 반환. |
| 10 | `MultiDocumentAnalysisUseCase(...)` | 다음 의존성으로 use case 인스턴스 생성: `get_github_repository()`, `get_ai_analyzer()`, `get_zip_packager()`, `get_blob_storage()`, `get_card_builder()`. |
| 11 | `use_case.execute(input_dto)` | 아래 “3. MultiDocumentAnalysisUseCase 내부” 참고. |
| 12 | 성공 시 | `get_card_builder().build_download_card(...)` 로 Adaptive Card JSON 생성 후 200 반환. |
| 13 | 예외 시 | `MessageFactory.create_error_message(str(e))` 200 반환. |

정리하면: **진입은 function_app → http_handler.main 이고, 실제 비즈니스는 모두 `MultiDocumentAnalysisUseCase.execute()` 안에서 이루어진다.**

---

## 3. MultiDocumentAnalysisUseCase.execute() 내부 (핵심 로직)

파일: `src/application/use_cases/multi_doc_analysis.py`

### 3.1 공통 (분기 전)

1. **URL 파싱**  
   `GitHubURL(value=input_dto.github_url)` 로 도메인 값 객체 생성.
2. **메타데이터 조회**  
   `self.github_repository.fetch_metadata(github_url)` → 레포 이름·설명 등 (Blob 업로드 시 컨테이너/이름 등에 사용).

### 3.2 문서 생성 (ai-agent 파이프라인 고정)

현재 프로젝트는 **항상 ai-agent 파이프라인만** 사용한다.

- `get_ai_analyzer()` → 항상 `AiAgentPipelineAdapter` 인스턴스를 반환.
- `MultiDocumentAnalysisUseCase.execute()`는 무조건 `self.ai_analyzer.run_from_url(github_url.value)` 를 호출해 5개 문서를 생성한다.
- 단일 LLM(MultiDocumentAnalyzer) 경로는 사용하지 않는다.

### 3.3 문서 생성 이후 (공통)

| 단계 | 처리 |
|------|------|
| 1 | `doc_data`에서 5개 문서 문자열을 꺼내 `documents = {"api_spec.md": ..., "erd.md": ..., "architecture.md", "tech_stack.md", "schema.sql"}` 형태로 만듦. |
| 2 | `self.zip_packager.create_zip(documents)` → ZIP 바이트. |
| 3 | `repo_name = f"{metadata.owner}-{metadata.name}"` 로 Blob 이름 결정. |
| 4 | `self.blob_storage.upload_zip(zip_bytes, repo_name)` → 업로드 후 SAS URL 등이 담긴 결과 객체. |
| 5 | `MultiDocumentAnalysisOutput(zip_blob_url=..., summary=..., document_count=5, expires_in_seconds=...)` 반환. |

이 출력이 다시 `http_handler`로 돌아가서, `build_download_card(..., download_url=result.zip_blob_url, ...)` 에 넘어가고, 그 카드 JSON이 최종 HTTP 응답이 된다.

---

## 4. AiAgentPipelineAdapter.run_from_url() (agents 경로 상세)

파일: `src/infrastructure/services/ai_agent_pipeline.py`

### 4.1 준비

- 임시 디렉터리 `out_root` 생성.
- `DOC_OUTPUT_DIR`, `CACHE_DIR` 환경변수를 이 경로로 설정 (erd_agent 등이 사용).
- `sys.path`에 `src/agents` 추가 후, `erd_agent.repo`, `erd_agent.commands.erd`, `api_agent.run`, `arch_agent.run`, `ddl_agent.run`, `stack_agent.run` import.

### 4.2 레포 준비

- `prepare_repo(github_url)` 호출 (erd_agent.repo).
  - GitHub URL이면: zip 다운로드 후 압축 해제, 캐시 디렉터리에 복사.
  - 로컬 경로면: 해당 경로 그대로 사용.
- 반환된 `repo_path` (로컬 디렉터리 Path)를 아래 에이전트에 넘김.

### 4.3 5개 에이전트 순차 실행

각 에이전트는 `(repo=repo_path, out_dir=...)` 형태로 호출된다. 실패한 에이전트는 로그만 남기고 다음으로 진행.

| 순서 | 에이전트 | 함수 | 출력 디렉터리 | 생성 파일 예시 |
|------|----------|------|----------------|----------------|
| 1 | erd | run_erd | out_root/erd | database.dbml, erd_summary.md |
| 2 | api | run_api | out_root/api | api_spec.md |
| 3 | arch | run_arch | out_root/arch | architecture.md |
| 4 | ddl | run_ddl | out_root/ddl | schema.sql |
| 5 | stack | run_stack | out_root/stack | tech_stack.md |

### 4.4 각 에이전트 내부: 스캐너 → 추출기 → 작성기 (관련 파일만 사용)

**USE_AI_AGENT=true** 이면 5개 에이전트가 **각자 전용 스캐너**로 레포에서 **관련 있는 파일만** 골라서 쓴다. 파일명/어노테이션 기준으로 필터링한다.

| 에이전트 | 스캐너 (관련 파일 추출) | 추출기 | 작성기 | 추출 대상 요약 |
|----------|-------------------------|--------|--------|----------------|
| **api** | `api_agent.scanner.scan_controller_files(repo_path)` | ai_extract_api | write_api_spec | `@RestController`, `@Controller`, `*Controller.java`, `*Resource.java`, `*Api.java` 등이 **포함된 Java 파일만** |
| **erd** | `erd_agent.scanner.scan_repo(repo_path)` | JPA 파서 또는 ai_extract_schema | write_dbml, write_summary_md | `@Entity`, `*Entity.java`, (옵션) `@Table` 등 **JPA 엔티티 후보만**. enum/embeddable 참조도 스캐너로 추가 수집 |
| **arch** | `arch_agent.scanner.scan_arch_files(repo_path)` | ai_extract_architecture | write_architecture | **설정/빌드 파일** (pom.xml, build.gradle, application.yml, Dockerfile 등) + **Spring/설정 관련 어노테이션**이 있는 Java (`@SpringBootApplication`, `@Configuration`, `@Service` 등) |
| **ddl** | erd_agent.scanner 동일 (scan_repo + enum/embeddable) | ai_extract_ddl | write_ddl | ERD와 동일하게 **JPA 엔티티·enum·embeddable** 관련 파일만 |
| **stack** | `stack_agent.scanner.scan_stack_files(repo_path)` | ai_extract_stack | write_stack | **빌드·의존성·설정 파일만** (pom.xml, package.json, requirements.txt, docker-compose.yml, .github/workflows 등) |

- **api_agent/scanner.py** 예: `@RestController`, `@Controller`, `@GetMapping` 등이 **포함된** Java 파일, 또는 파일명이 `*Controller.java`, `*Resource.java`, `*Api.java` 인 파일만 리스트에 넣는다. 그 리스트만 추출기(LLM)에 넘긴다.
- **erd_agent/scanner.py**: `@Entity` 또는 `*Entity.java` 등 JPA 엔티티 후보만; 필요 시 enum/embeddable 정의 파일도 찾아서 추가한다.
- **arch_agent/scanner.py**: CONFIG_FILES 이름 매칭 + Java 내용에 ARCH_HINTS_RE(Spring/설정 어노테이션) 있는 파일만.
- **stack_agent/scanner.py**: BUILD_FILES 이름 집합 + `.github/workflows/*.yml` 등만.

즉, **에이전트마다 스캐너가 “이 에이전트에 관련있는 파일”만 추출**하고, 그 다음 단계(추출기/작성기)는 그 파일들만 본다.

### 4.5 5개 문서 수집 (매핑 없음)

- `_collect_documents(out_root, repo_path.name)`:
  - 5개 에이전트 산출물만 읽어 `api_spec`, `erd`, `architecture`, `tech_stack`, `schema_sql` + `project_summary` dict 구성.
  - 7 doc 형식 매핑·플레이스홀더 없이, 생성된 5개 결과만 반환.
- 이 dict가 `run_from_url()` 반환값이 되고, use case의 `doc_data`로 사용된다.

---

## 5. 단일 LLM 경로 (MultiDocumentAnalyzer)

파일: `src/infrastructure/services/multi_doc_analyzer.py`

- **입력**: `RepositoryAnalysis` (metadata, file_tree, source_files 등).
- **클라이언트**: `aoai_client.build_aoai_client(endpoint, api_key, api_version, deployment)` 로 OpenAI/AzureOpenAI 클라이언트 생성.
- **호출**: 한 번의 `chat.completions.create()`로 시스템 프롬프트 + 사용자 프롬프트(파일 트리 + 소스 내용 요약) 전달.
- **응답**: JSON 한 번에 7개 문서 + project_summary 요청 (단일 LLM 경로용. 현재는 미사용).

---

## 6. GitHub 레포 데이터 (단일 LLM 경로에서만 사용)

파일: `src/infrastructure/repositories/github.py` (PyGitHubRepository)

- **fetch_metadata**: 레포 이름, 언어, 설명 등.
- **fetch_file_tree**: 디렉터리/파일 트리 (이름만).
- **fetch_source_files**: “핵심 파일”만 최대 30개, 파일당 5000자.  
  - 경로/파일명 패턴(controller, entity, service, config 등)으로 필터.
  - 확장자: 코드·설정 파일만.

agents 경로에서는 이 단계를 건너뛰고 `run_from_url`에서 `prepare_repo`로 직접 zip/로컬만 사용한다.

---

## 7. ZIP · Blob · 카드

- **ZIP**: `src/infrastructure/services/zip_packager.py` — 5개 파일(api_spec.md, erd.md, architecture.md, tech_stack.md, schema.sql)을 ZIP 바이트로 패키징.
- **Blob**: `src/infrastructure/services/blob_storage.py` — Azure Blob에 업로드 후 SAS URL 생성.
- **카드**: `src/infrastructure/services/card.py` (TeamsCardBuilder) — `build_download_card(summary, download_url, document_count, expires_in_seconds)` 로 Bot Framework용 Adaptive Card JSON 생성.

---

## 8. 환경 변수와 설정

- **로컬**: `.env` 한 곳만 사용. `http_handler` 진입 시 `load_dotenv(_env_path)`로 로드.
- **항목**:  
  `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_KEY`, `OPENAI_API_VERSION`, `AZURE_OPENAI_DEPLOYMENT`,  
  `USE_AI_AGENT`, `AZURE_STORAGE_CONNECTION_STRING`, `AZURE_BOT_ID`, `AZURE_BOT_PASSWORD`, `GITHUB_TOKEN` 등.
- **local.settings.json**: `func start`용 최소 설정만 (FUNCTIONS_WORKER_RUNTIME, AzureWebJobsStorage 등). 앱 로직은 `.env`만 본다.

---

## 9. 삭제된 것 (정리)

- **app/** 폴더: 예전 진입점 `app/main.py` 및 그에 딸린 config, services, models.  
  현재 진입점은 `function_app.py` → `src/.../http_handler.main` 이므로 사용하지 않아 제거함.
- **http_handler** 에서 사용하지 않는 import (DiagramRenderer, MermaidInkRenderer, AzureOpenAIService 등) 제거함.

---

## 10. 요약 다이어그램

```
[Teams / HTTP POST]  →  function_app.messages(req)
                              ↓
                    http_handler.main(req)
                              ↓
                    parse_teams_activity → type=="message", text
                              ↓
                    help? → help 메시지 반환
                    URL 없음? → github_not_found 반환
                              ↓
                    MultiDocumentAnalysisInput 검증
                              ↓
                    MultiDocumentAnalysisUseCase.execute(input_dto)
                      ├─ fetch_metadata (항상)
                      ├─ [USE_AI_AGENT] run_from_url → prepare_repo → 5 agents → _collect_and_map
                      └─ [else] fetch_file_tree, fetch_source_files → analyze → doc_data
                      ├─ documents dict 구성
                      ├─ zip_packager.create_zip
                      ├─ blob_storage.upload_zip
                      └─ MultiDocumentAnalysisOutput 반환
                              ↓
                    build_download_card(...)  →  HTTP 200 JSON (Adaptive Card)
```

이 문서만 따라가면, “시작이 어디인지”, “요청이 어떻게 흐르는지”, “agents와 단일 LLM이 어디서 갈라지는지”까지 전부 코드와 1:1로 대응할 수 있다.
