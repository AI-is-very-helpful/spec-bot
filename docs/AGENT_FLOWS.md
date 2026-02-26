# 각 AI Agent 문서 생성 흐름 (스캐너 → 추출기 → 작성기)

5개 에이전트는 모두 **스캐너(어떤 파일을 볼지)** → **추출기(내용 분석)** → **작성기(문서 출력)** 순서로 동작합니다.  
아래는 에이전트별로 **어떤 어노테이션/파일을 찾고, 어떤 흐름으로 문서를 만드는지** 그림으로 정리한 내용입니다.

---

## 공통 패턴

```
  [로컬 레포 repo_path]
           │
           ▼
  ┌─────────────────┐
  │    Scanner      │  ← 파일명/어노테이션으로 "대상 파일 목록"만 추림
  └────────┬────────┘
           │ List[Path]
           ▼
  ┌─────────────────┐
  │   Extractor     │  ← 선택된 파일 내용을 분석 (LLM 또는 파서)
  └────────┬────────┘
           │ 구조화된 데이터 (JSON/모델)
           ▼
  ┌─────────────────┐
  │    Writer       │  ← Markdown / DBML / SQL 등 최종 문서 파일 생성
  └────────┬────────┘
           │
           ▼
  [api_spec.md / database.dbml / architecture.md / schema.sql / tech_stack.md]
```

---

## 1. API Agent (api_spec.md)

**역할**: REST API 스펙 문서 생성.

### Scanner — 어떤 파일을 찾는가

- **어노테이션**: `@RestController`, `@Controller`, `@RequestMapping`, `@GetMapping`, `@PostMapping`, `@PutMapping`, `@DeleteMapping`, `@PatchMapping` **중 하나라도 포함된** `.java` 파일
- **파일명**: `*Controller.java`, `*Resource.java`, `*Api.java` (대소문자 무시)
- **동작**: 레포 전체 `rglob("*.java")` 후, 위 정규식으로 필터 → **Controller 후보 목록** 반환

```
  repo_path
       │
       ▼  rglob("*.java") → 각 파일 read_text()
  ┌──────────────────────────────────────────────────────────┐
  │  CONTROLLER_ANN_RE: @RestController|@Controller|@GetMapping|...
  │  CONTROLLER_NAME_RE: .*Controller\.java$ | .*Resource\.java$ | .*Api\.java$
  └──────────────────────────────────────────────────────────┘
       │
       ▼  매칭된 파일만 List[Path]
  controller_files
```

### Extractor — 어떻게 분석하는가

- **입력**: `(Path, content)` 리스트 (스캐너가 고른 Controller 파일들)
- **방식**: Azure OpenAI LLM 호출. 프롬프트에 위 파일 내용을 `<file path="...">` 형태로 넣음.
- **규칙**: `@RequestMapping` → base path, `@GetMapping`/`@PostMapping` 등 → method+path, `@PathVariable`/`@RequestParam`/`@RequestBody` → 파라미터/요청체, 반환 타입/`ResponseEntity` → 응답
- **출력**: JSON → `ExtractedApiSpec` (controllers[].endpoints[])

```
  controller_files + 내용
       │
       ▼
  ┌─────────────────┐     System + User prompt (파일 내용)
  │  ai_extract_api │ ──► Azure OpenAI (JSON 모드)
  └────────┬────────┘
           │ ExtractedApiSpec { controllers: [ { name, base_path, endpoints[] } ] }
           ▼
```

### Writer — 어떤 문서를 만드는가

- **입력**: `ExtractedApiSpec`
- **출력**: `api_spec.md` — 컨트롤러별 섹션, 각 엔드포인트에 `method`, `path`, 파라미터 테이블, request/response body, status

```
  ExtractedApiSpec
       │
       ▼  to_markdown(spec)
  write_api_spec(spec, out_path)  →  api_spec.md
```

---

## 2. ERD Agent (database.dbml, erd_summary.md)

**역할**: JPA 엔티티 기준 ERD(DBML + 요약 MD) 생성.

### Scanner — 어떤 파일을 찾는가

- **1) 엔티티 후보**
  - **어노테이션**: `@Entity` 포함 `.java` → 우선 수집
  - **파일명**: `*Entity.java` (보조)
  - **옵션**: `@Table`만 있어도 수집 (include_table_only=True 시)
- **2) 엔티티에서 참조하는 타입 추가 수집**
  - **Enum**: 엔티티 본문에서 `@Enumerated(EnumType.STRING) @Column ... private Role role` 등 → `Role` 같은 enum 타입명 추출 → 레포에서 `enum Role { ... }` 정의된 파일 검색해 추가
  - **Embeddable**: 엔티티 본문에서 `@EmbeddedId private PayId id` → `PayId` 추출 → `@Embeddable` + `class PayId` / `record PayId` 정의된 파일 검색해 추가
- **우선 탐색 디렉터리**: `models`, `model`, `entity`, `entities`, `domain` (그 다음 전체 `rglob("*.java")`)

```
  repo_path
       │
       ├─ prefer_dirs (models, entity, ...) + rglob("*.java")
       │       │
       │       ▼  ENTITY_ANN_RE (@Entity) / ENTITY_NAME_RE (*Entity.java) / @Table
       │  entity_files
       │
       ├─ entity 파일 내용에서
       │     ENUM_FIELD_RE, EMBEDDED_ID_TYPE_RE  →  enum/embeddable 타입 이름 수집
       │       │
       │       ▼  find_enum_definition_files / find_embeddable_definition_files
       │  enum_files, embeddable_files
       │
       ▼
  entity_files + enum_files + embeddable_files  (전부 합쳐서 추출기 입력)
```

### Extractor — 어떻게 분석하는가

- **ai_first=True**: 위에서 모은 **전체 파일**을 LLM(`ai_extract_schema`)에 넘겨서 JSON 스키마 추출 → `Schema` (tables, refs, enums)
- **ai_first=False**: **JPA 파서**(`JPAJavaParser`)로 엔티티 파일만 파싱 → `Schema` 구성. 옵션으로 `refine_schema_with_aoai` 호출 가능
- **규칙**: `@Entity`→테이블, `@Table(name)`→테이블명, `@Id`/`@Column`→컬럼, `@ManyToOne`/`@JoinColumn`→FK, `@ManyToMany`/`@JoinTable`→조인 테이블, `@EmbeddedId`→@Embeddable 필드 전개

```
  entity + enum + embeddable 파일들
       │
       ├─ [ai_first]  ai_extract_schema(...)  →  Schema (LLM JSON → 모델)
       │
       └─ [파서 경로]  JPAJavaParser.parse(...)  →  Schema
                       (선택) refine_schema_with_aoai(schema)
       │
       ▼  normalize_schema(schema)
  Schema
```

### Writer — 어떤 문서를 만드는가

- **write_dbml(schema, dbml_path)** → `database.dbml` (테이블, 컬럼, Ref)
- **write_summary_md(schema, md_path)** → `erd_summary.md` (요약 설명)

```
  Schema
       │
       ├─ write_dbml        →  database.dbml
       └─ write_summary_md  →  erd_summary.md
```

---

## 3. Arch Agent (architecture.md)

**역할**: 아키텍처 스타일·레이어·의존성·Mermaid 다이어그램 문서 생성.

### Scanner — 어떤 파일을 찾는가

- **고정 파일명**: `pom.xml`, `build.gradle`, `application.yml`, `application.properties`, `Dockerfile`, `docker-compose.yml`, `package.json`, `requirements.txt`, `go.mod` 등 (`CONFIG_FILES` 집합)
- **Java 파일**: 본문에 다음 **어노테이션 중 하나라도 있으면** 수집  
  `@SpringBootApplication`, `@Configuration`, `@Service`, `@Repository`, `@Controller`, `@RestController`, `@EnableJpaRepositories`, `@EnableWebSecurity`, `@EnableFeignClients`, `@EnableKafka`, `@EnableCaching` 등 (`ARCH_HINTS_RE`)
- **추가**: `collect_directory_tree(repo_path)` 로 디렉터리 트리 문자열 생성 (max_depth 4, .git/node_modules/target 등 제외)

```
  repo_path
       │
       ├─ rglob("*")  →  파일명 in CONFIG_FILES  ⇒  추가
       ├─ *.java      →  ARCH_HINTS_RE 검색     ⇒  매칭 시 추가
       └─ collect_directory_tree(repo_path)     ⇒  dir_tree 문자열
       │
       ▼
  arch_files + dir_tree
```

### Extractor — 어떻게 분석하는가

- **입력**: `(arch_files 내용)` + `dir_tree`
- **방식**: LLM 한 번 호출. 디렉터리 구조 + 선택된 파일 내용을 주고, 아키텍처 스타일·레이어·의존성·외부 시스템·Mermaid flowchart JSON 요청
- **출력**: `ExtractedArchitecture` (architecture_style, layers, dependencies, external_systems, mermaid_diagram)

```
  file_texts + dir_tree
       │
       ▼  USER_PROMPT (dir_tree + files_blob)
  ┌─────────────────────────┐
  │ ai_extract_architecture │ ──► Azure OpenAI (JSON)
  └────────────┬────────────┘
               │ ExtractedArchitecture
               ▼
```

### Writer — 어떤 문서를 만드는가

- **write_architecture(arch, out_path)** → `architecture.md` (스타일, 요약, 레이어, 의존성, 외부 시스템, Mermaid 코드 블록)

```
  ExtractedArchitecture
       │
       ▼  write_architecture(arch, out_path)
  architecture.md
```

---

## 4. DDL Agent (schema.sql)

**역할**: JPA 엔티티 → CREATE TABLE 등 DDL(SQL) 생성.

### Scanner — 어떤 파일을 찾는가

- **ERD Agent와 동일**: `scan_repo(repo_path)` → `@Entity` / `*Entity.java` 등 엔티티 후보
- **추가 수집**: 엔티티 내용에서 `@Enumerated` enum 타입명, `@EmbeddedId` 타입명 추출 → 해당 **enum 정의 파일**, **@Embeddable 정의 파일** 검색해 리스트에 추가
- 즉, **ERD와 같은 “엔티티 + enum + embeddable” 파일 집합**을 추출기 입력으로 사용

```
  repo_path
       │
       ▼  scan_repo (entity) + find_enum_* + find_embeddable_*
  entity_files + enum_files + embeddable_files
```

### Extractor — 어떻게 분석하는가

- **입력**: 위에서 모은 전체 파일 내용
- **방식**: LLM(`ai_extract_ddl`) 한 번 호출. JPA 규칙(@Entity→CREATE TABLE, @Column→컬럼, @ManyToOne→FK 등) 주고 JSON DDL 스키마 요청
- **출력**: `ExtractedDDL` (dialect, tables[].columns, constraints 등)

```
  entity + enum + embeddable 파일들
       │
       ▼  USER_PROMPT (JPA → DDL 규칙)
  ┌─────────────────┐
  │ ai_extract_ddl  │ ──► Azure OpenAI (JSON)
  └────────┬────────┘
           │ ExtractedDDL { dialect, tables[] }
           ▼
```

### Writer — 어떤 문서를 만드는가

- **write_ddl(ddl, out_path)** → `schema.sql` (CREATE TABLE, PRIMARY KEY, FOREIGN KEY 등)

```
  ExtractedDDL
       │
       ▼  write_ddl(ddl, out_path)
  schema.sql
```

---

## 5. Stack Agent (tech_stack.md)

**역할**: 빌드·의존성·설정 파일 기준 기술 스택 문서 생성.

### Scanner — 어떤 파일을 찾는가

- **고정 파일명만** 사용 (내용 검사 없음):
  - 빌드: `pom.xml`, `build.gradle`, `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, `Gemfile`, `Makefile`, `CMakeLists.txt` 등
  - 설정: `application.yml`, `application.properties`, `Dockerfile`, `docker-compose.yml`, `.env.example` 등
  - CI: `.github/workflows/*.yml` (경로가 `.github/workflows`로 시작하고 확장자 `.yml`/`.yaml`)
- **동작**: `rglob("*")` 후 파일명/상대경로가 위 조건에 맞으면 추가 → **List[Path]** 반환

```
  repo_path
       │
       ▼  rglob("*")  →  f.name in BUILD_FILES  OR  rel.startswith(".github/workflows") && .yml/.yaml
  stack_files
```

### Extractor — 어떻게 분석하는가

- **입력**: 스캐너가 고른 파일들의 내용
- **방식**: LLM 한 번 호출. 언어/버전, 프레임워크, 빌드 도구, 의존성 카테고리별 목록(이름·버전·scope·설명) JSON 요청
- **출력**: `ExtractedStack` (language, framework, build_tool, categories[])

```
  stack_files 내용
       │
       ▼  USER_PROMPT (build/dependency 파일 내용)
  ┌─────────────────┐
  │ ai_extract_stack │ ──► Azure OpenAI (JSON)
  └────────┬────────┘
           │ ExtractedStack
           ▼
```

### Writer — 어떤 문서를 만드는가

- **write_stack(stack, out_path)** → `tech_stack.md` (언어, 프레임워크, 빌드 도구, 카테고리별 의존성 표 등)

```
  ExtractedStack
       │
       ▼  write_stack(stack, out_path)
  tech_stack.md
```

---

## 요약 표

| 에이전트 | Scanner 기준 (어노테이션/파일명) | Extractor | Writer 출력 |
|----------|----------------------------------|-----------|-------------|
| **API** | `@RestController`/`@Controller`/`@GetMapping` 등, `*Controller.java` | LLM (JSON) | api_spec.md |
| **ERD** | `@Entity`, `*Entity.java`, enum/embeddable 참조 파일 추가 | LLM 또는 JPA 파서 → Schema | database.dbml, erd_summary.md |
| **Arch** | CONFIG_FILES 이름 + Java에 `@SpringBootApplication` 등 ARCH_HINTS + 디렉터리 트리 | LLM (JSON) | architecture.md |
| **DDL** | ERD와 동일 (entity + enum + embeddable) | LLM (JSON) | schema.sql |
| **Stack** | BUILD_FILES 이름 + `.github/workflows/*.yml` | LLM (JSON) | tech_stack.md |

*이 문서는 `src/agents/` 내 각 에이전트의 `scanner.py`, `extractor.py`, `writer.py`, `run.py` 및 erd_agent `commands/erd.py`를 기준으로 작성했습니다.*
