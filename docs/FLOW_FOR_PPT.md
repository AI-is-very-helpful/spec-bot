# Spec Bot — Azure Function 수신 ~ 응답 (PPT용 구조)

아래는 **Azure Function이 요청을 받는 시점부터 최종 응답을 내보내는 시점까지**의 흐름을, 슬라이드 단위로 나눠 둔 문서입니다. 각 `---` 구간을 한 장(또는 한 블록)으로 쓰면 됩니다.

---

## 슬라이드 1: 제목

**Spec Bot 처리 흐름**  
Azure Function 수신 → 응답까지

---

## 슬라이드 2: 진입

**1. Azure Function이 요청을 받는다**

- **엔드포인트**: `POST /api/messages`
- **진입 코드**: `function_app.py` → `messages(req)` → `http_handler_main(req)`
- **요청 Body**: Teams/Bot이 전달하는 JSON (예: `type`, `text`, `from`, `conversation` 등)

```
[Teams/Bot] → POST /api/messages (JSON) → [Azure Function] → http_handler.main(req)
```

---

## 슬라이드 3: 요청 파싱

**2. 요청 Body 파싱 & 메시지 여부 확인**

- `req.get_json()` → Body를 dict로 파싱
- `TeamsBotService.parse_teams_activity(req_body)` 호출
  - `type == "message"` 인지 확인
  - 아니면 → **즉시 응답**: `{"status": "OK"}` (200) 후 종료
- 메시지면 `activity["text"]` 에 사용자 입력 문자열 보관

---

## 슬라이드 4: 도움말 / URL 추출

**3. 도움말인지, GitHub URL인지 판별**

- **도움말**: `is_help_command(message)` → "help", "도움말" 등
  - **응답**: 도움말 메시지 JSON (200) 후 종료
- **URL 추출**: `extract_github_url(message)` → 정규식으로 `https://github.com/owner/repo` 추출
  - URL 없으면 → **응답**: "GitHub URL을 찾을 수 없습니다" 메시지 (200) 후 종료
- URL 있으면 → 다음 단계(유스케이스)로 진행

---

## 슬라이드 5: 입력 검증

**4. 입력 검증 후 유스케이스 준비**

- `MultiDocumentAnalysisInput(github_url=repo_url)` 로 Pydantic 검증
  - 실패 시 → **응답**: 에러 메시지 (200) 후 종료
- 성공 시 `MultiDocumentAnalysisUseCase` 인스턴스 생성
  - 주입: GitHub 레포, AI 분석기(ai-agent 파이프라인), ZIP 패키저, Blob 스토리지, 카드 빌더
- `use_case.execute(input_dto)` 호출 → **핵심 처리** 진입

---

## 슬라이드 5-1: HTTP Handler 다음에 누가 받나? (전체 흐름 한눈에)

**질문**: Azure Functions → HTTP Handler 다음에 **누가** 받나?

**답**: **유스케이스 (MultiDocumentAnalysisUseCase)** 가 받습니다.  
HTTP Handler가 `use_case.execute(input_dto)` 를 호출하면, 그때부터는 **유스케이스**가 흐름을 이어갑니다.

**전체 순서 (PPT용)**

```
1. Azure Functions        → POST /api/messages 수신
2. HTTP Handler          → 파싱·URL 추출·검증 후 use_case.execute() 호출
3. 유스케이스             → 여기서부터 유스케이스가 처리
   ├─ 메타데이터 조회      → GitHub API로 owner/name만 (Blob 이름용)
   ├─ 문서 생성 요청      → ai_analyzer.run_from_url(github_url) 호출
   │     │
   │     └─ AiAgentPipelineAdapter (문서 생성 담당)
   │           ├─ 레포 준비  → prepare_repo(URL): GitHub **zip 다운로드** (git clone 아님) → 로컬 경로
   │           ├─ 5개 에이전트 순차 실행 → 5개 문서 내용 수집
   │           └─ doc_data 반환
   │
   ├─ 5개 문서 → ZIP 패키징
   ├─ ZIP → Blob Storage 업로드 (SAS URL 발급)
   └─ 결과(URL, 요약 등) 반환
4. HTTP Handler          → 반환된 결과로 Adaptive Card 만들고 HTTP 200 응답
```

**정리**

- **HTTP Handler 다음** = **유스케이스**가 받아서, 메타 조회 → **문서 생성(ai_analyzer)** → ZIP → Blob 까지 한 번에 수행.
- **레포 가져오기** = **git clone이 아니라** GitHub **zip 다운로드** 후 압축 해제 (`prepare_repo`). 그 로컬 경로를 5개 에이전트가 사용합니다.
- **문서 생성** = 유스케이스가 **AiAgentPipelineAdapter.run_from_url()** 한 번 호출하고, 그 안에서 prepare_repo → 5 에이전트 → 5개 문서 dict 반환.

---

## 슬라이드 6: 유스케이스 ① 메타 & 문서 생성

**5. 유스케이스 내부 (1) — 메타데이터 & 문서 생성**

- **URL 파싱**: `GitHubURL(value=github_url)` 로 입력 검증(값 객체 생성).
- **메타데이터 조회**: `github_repository.fetch_metadata(github_url)`  
  → **레포 파일을 가져오는 것이 아님.** GitHub API로 **owner, name 정도만** 조회.  
  → 용도: 나중에 Blob 업로드 시 ZIP 파일명을 `owner-repo` 형태로 쓰기 위함.
- **문서 생성**: `ai_analyzer.run_from_url(github_url)`  
  → **여기서** 레포를 실제로 다운로드함.  
  → 파이프라인 내부에서 `prepare_repo(github_url)` 로 **zip 다운로드 → 로컬 경로** 확보 후, **그 로컬 파일들**을 기준으로 5개 에이전트가 스캔·분석 → **5개 문서**가 담긴 `doc_data` dict 반환.

---

## 슬라이드 7: ai-agent 파이프라인 개요

**6. ai-agent 파이프라인 (run_from_url) 개요**

*(슬라이드 6의 "문서 생성" 단계가 호출하는 흐름)*

- **레포 준비**: `prepare_repo(github_url)`  
  → **git clone이 아니라 GitHub zip 다운로드** 후 압축 해제. (또는 로컬 경로면 그대로 사용) → `repo_path` 확보
- **5개 에이전트 순차 실행** (각자 스캐너로 관련 파일만 추출 후 LLM/작성기 사용)
  - ERD → database.dbml, erd_summary.md
  - API → api_spec.md
  - Arch → architecture.md
  - DDL → schema.sql
  - Stack → tech_stack.md
- **5개 문서만 반환**: 위 결과를 그대로 `api_spec`, `erd`, `architecture`, `tech_stack`, `schema_sql` + `project_summary` dict로 반환 (매핑/플레이스홀더 없음)

---

## 슬라이드 7-1: Scanner / Extractor / Writer 정의 (PPT용 한 줄)

| 단계 | 정의 (PPT에 그대로 쓸 문장) |
|------|-----------------------------|
| **Scanner** | 레포에서 **이 에이전트에 해당하는 파일만** 추출한다. 어노테이션(`@Entity`, `@RestController` 등) 또는 파일명 패턴(`*Controller.java`, `pom.xml` 등)으로 필터링해 **대상 파일 목록**을 만든다. |
| **Extractor** | Scanner가 고른 파일 내용을 **청크(글자 수 제한) 단위로 나눈 뒤**, 프롬프트와 함께 **Azure OpenAI에 분석 요청**을 보낸다. 청크별로 받은 JSON을 **병합**해 하나의 **구조화 데이터**(API 스펙, 스키마, 아키텍처 등)로 만든다. |
| **Writer** | Extractor가 반환한 **구조화 데이터(JSON/모델)**를 받아 **최종 문서 파일**로 변환·저장한다. Markdown(`.md`), DBML, SQL 등 형식으로 디스크에 쓴다. |

**짧게 쓸 때 (불릿용)**

- **Scanner** = 레포에서 관련 파일만 추출 (어노테이션·파일명 패턴)
- **Extractor** = 프롬프트 + 파일(청크)로 Azure OpenAI 분석 요청 → 구조화 데이터(JSON) 수집·병합
- **Writer** = 구조화 데이터 → 문서 파일(MD/DBML/SQL) 생성·저장

---

## 슬라이드 7-2: 각 에이전트 공통 흐름 (스캐너 → 추출기 → 작성기)

**에이전트 하나당 흐름**

```
  [로컬 레포]
       │
       ▼  Scanner: 어노테이션/파일명으로 "볼 파일만" 추림 → List[Path]
  List[Path]
       │
       ▼  Extractor: 파일 내용(청크) + 프롬프트 → Azure OpenAI → JSON 병합
  구조화 데이터 (JSON/모델)
       │
       ▼  Writer: JSON/모델 → Markdown·DBML·SQL 등 문서 파일로 저장
  [문서 파일]
```

**상세 흐름(어떤 어노테이션을 찾고 어떻게 문서를 만드는지)** → `docs/AGENT_FLOWS.md` 참고.

---

## 슬라이드 7-3: 에이전트별 스캔 기준 & 출력 요약

| 에이전트 | Scanner가 찾는 것 | Extractor | 출력 파일 |
|----------|-------------------|-----------|-----------|
| **API** | `@RestController`, `@GetMapping` 등 **포함**된 Java, 또는 `*Controller.java` | LLM → JSON (엔드포인트 목록) | api_spec.md |
| **ERD** | `@Entity` / `*Entity.java` + 참조된 **enum**·**@Embeddable** 정의 파일 | LLM 또는 JPA 파서 → Schema | database.dbml, erd_summary.md |
| **Arch** | **설정/빌드 파일명** (pom.xml, application.yml, Dockerfile 등) + Java에 `@SpringBootApplication` 등 | LLM + **디렉터리 트리** | architecture.md |
| **DDL** | ERD와 동일 (entity + enum + embeddable) | LLM → DDL 스키마 JSON | schema.sql |
| **Stack** | **빌드/의존성 파일명** (pom.xml, package.json, requirements.txt 등) + `.github/workflows/*.yml` | LLM → 기술 스택 JSON | tech_stack.md |

*(그림 포함 상세 흐름: `docs/AGENT_FLOWS.md`)*

---

## 슬라이드 8: ZIP & Blob & 출력

**7. 유스케이스 내부 (2) — ZIP 패키징 & Blob 업로드**

- `doc_data`에서 5개 문서 문자열을 꺼내 `documents` dict 생성 (파일명 → 내용)
- `zip_packager.create_zip(documents)` → ZIP 바이트 생성
- `blob_storage.upload_zip(zip_bytes, repo_name)`  
  → Azure Blob 업로드 후 **SAS URL** 등이 담긴 결과 객체 획득
- `MultiDocumentAnalysisOutput(zip_blob_url=..., summary=..., document_count=5, expires_in_seconds=...)` 반환

---

## 슬라이드 9: 성공 시 응답

**8. 성공 시 최종 응답**

- 유스케이스가 정상 반환하면 `http_handler`에서:
  - `card_builder.build_download_card(summary, download_url=zip_blob_url, document_count, expires_in_seconds)` 호출
  - → **Adaptive Card** JSON 생성 (다운로드 버튼 + 요약)
- `func.HttpResponse(json.dumps(card), mimetype="application/json", status_code=200)`  
  → **이 JSON이 Azure Function의 최종 응답** (Teams/Bot이 카드로 렌더링)

---

## 슬라이드 10: 실패 시 응답

**9. 실패 시 응답**

- 유스케이스 실행 중 예외 발생 시:
  - `MessageFactory.create_error_message(str(e))` 로 에러 메시지 JSON 생성
  - `func.HttpResponse(..., status_code=200)` 로 **동일하게 200 + JSON** 반환 (Bot 규약 유지)

---

## 슬라이드 11: 전체 흐름 요약

**10. 전체 흐름 요약 (한 장)**

```
[요청] POST /api/messages (Teams Activity JSON)
    ↓
[파싱] type=="message" ? → text 추출
    ↓
[분기] 도움말? → 도움말 응답
       URL 없음? → "URL 찾을 수 없음" 응답
    ↓
[검증] MultiDocumentAnalysisInput(github_url)
    ↓
[실행] MultiDocumentAnalysisUseCase.execute()
    ├─ fetch_metadata (GitHub API)
    ├─ run_from_url (prepare_repo → 5 agents → 5 doc 반환)
    ├─ create_zip (5개 파일 → ZIP)
    └─ upload_zip (Blob → SAS URL)
    ↓
[응답] build_download_card → HTTP 200 + Adaptive Card JSON
      (또는 예외 시 에러 메시지 JSON)
```

---

## 슬라이드 12: 담당 모듈

**11. 구간별 담당 모듈**

| 구간 | 담당 |
|------|------|
| 진입 | `function_app.py`, `http_handler.main` |
| 파싱/도움말/URL | `TeamsBotService`, `MessageFactory` |
| 검증 | `MultiDocumentAnalysisInput` (Pydantic) |
| 메타 조회 | `PyGitHubRepository.fetch_metadata` |
| 문서 생성 | `AiAgentPipelineAdapter.run_from_url` → `prepare_repo` + 5 agents |
| ZIP | `ZIPPackagingService.create_zip` |
| Blob | `AzureBlobStorageService.upload_zip` |
| 응답 카드 | `TeamsCardBuilder.build_download_card` |

---

*이 문서는 `docs/LOGIC_FLOW.md`를 PPT용으로 재구성한 것입니다. 슬라이드 수는 필요에 따라 묶거나 나누어 사용하면 됩니다.*
