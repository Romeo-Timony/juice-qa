# OWASP Juice Shop: Autonomous Enterprise QA Automation & QAOps Platform
## Master Project Review & System Reference Manual for Technical Interviews & AI Copilots

> **Target Audience:** Technical Interviewers, QA Architects, Lead SDETs, and AI Agents acting as Copilot.  
> **Key Philosophy:** Autonomous, zero-drift, human-in-the-loop (HITL) quality engineering platform combining deterministic static validation, multi-agent AI orchestration, and enterprise CI/CD integration.

---

## 📑 TABLE OF CONTENTS
1. [Executive Summary & Business Value](#1-executive-summary--business-value)
2. [Target System Under Test (SUT) Architecture](#2-target-system-under-test-sut-architecture)
3. [High-Level QA Platform Architecture: 2 Operational Contours](#3-high-level-qa-platform-architecture-2-operational-contours)
4. [Test Data Management & State Isolation (TDM)](#4-test-data-management--state-isolation-tdm)
5. [The 8-Stage Autonomous Lifecycle (End-to-End Walkthrough)](#5-the-8-stage-autonomous-lifecycle-end-to-end-walkthrough)
6. [Architecture Decision Records (DEC-001 through DEC-015)](#6-architecture-decision-records-dec-001-through-dec-015)
7. [PromptOps, LLM-as-a-Judge & Evaluation Framework](#7-promptops-llm-as-a-judge--evaluation-framework)
8. [4-Tier Qase TMS Deduplication & Idempotency Engine](#8-4-tier-qase-tms-deduplication--idempotency-engine)
9. [Static Code Gate & Anti-Flakiness Engineering](#9-static-code-gate--anti-flakiness-engineering)
10. [Observability, Resilience & Fallbacks](#10-observability-resilience--fallbacks)
11. [Top-15 Tricky Interview Questions & Master Answers](#11-top-15-tricky-interview-questions--master-answers)

---

## 1. EXECUTIVE SUMMARY & BUSINESS VALUE

### What is this project?
An enterprise-grade, event-driven autonomous QA automation harness designed to eliminate manual overhead in the test design, implementation, and verification lifecycle while maintaining 100% human accountability.

### Core Metrics & Capabilities:
- **Time to Production Tests:** Reduced from 1–2 days of manual test design & scripting to **< 3 minutes** from Jira ticket creation to running in CI.
- **Flaky Test Rate:** **0%** achieved through deterministic state isolation, database transaction rollback fixtures, and elimination of arbitrary sleep timers.
- **Traceability:** **100% bidirectional coverage** linking Confluence living specifications $\leftrightarrow$ Jira User Stories $\leftrightarrow$ Whimsical MindMaps $\leftrightarrow$ Qase TMS test suites $\leftrightarrow$ Pytest source code $\leftrightarrow$ Allure Reports.
- **Human Accountability:** 2 Human-in-the-Loop (HITL) gates prevent AI hallucinations from escaping into test designs (Gate 1) or codebases (Gate 2).

---

## 2. TARGET SYSTEM UNDER TEST (SUT) ARCHITECTURE

The target application is **OWASP Juice Shop** (v17+), the industry-standard intentionally vulnerable e-commerce web application.

* **Frontend:** Angular 21.x, Angular Material M3, RxJS, Single Page Application (SPA).
* **Backend:** Node.js (22–24 LTS), Express.js REST API.
* **Database & ORM:** SQLite file-backed database operated via Sequelize ORM.
* **Security & Tokens:** Stateless JSON Web Tokens (JWT) signed with HMAC-SHA256, `Bearer` authorization headers intercepted via Angular `JwtInterceptor`.
* **External Integrations:** Simulated payment gateways, file uploads (multer), and email servers. External dependencies and fault-injection are mocked via **WireMock Standalone** (`DEC-012`).

---

## 3. HIGH-LEVEL QA PLATFORM ARCHITECTURE: 2 OPERATIONAL CONTOURS

The architecture strictly decouples orchestration and human interaction from heavy code compilation and execution:

```
┌────────────────────────────────────────────────────────────────────────┐
│ CONTOUR 1: Cloud & Integration Orchestrator (n8n Cloud + Webhooks)    │
│  - Jira Cloud Webhooks & REST API (Transitions, Comments, Threads)     │
│  - Stage 0 Health Gate (7-service ping)                                │
│  - Stage 1 DoR Gate (INVEST scoring via Gemini Flash)                  │
│  - Whimsical MindMap text-to-diagram generation                       │
│  - Qase TMS BDD sync (Suite #86) & Deduplication                       │
│  - Telegram Bot Alerts (@QApower_bot) & HITL Wait Nodes                │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Bidirectional REST API / Daemon Polling
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│ CONTOUR 2: Local Python SDET & Heavy Engineering Engine                │
│  - Background Orchestration Daemon (`scripts/qa_agent_daemon.py`)      │
│  - Dynamic Test Scaffolder (`scripts/scaffold_dynamic.py`)             │
│  - Seam 3 Static Code Gate (AST parse, Ruff E9/F82, Pytest collect)   │
│  - Isolated Sandbox Review Environment (`tests/review/`)               │
│  - Git Worktree Promotion & Idempotent Content Digest Push             │
│  - Test Runner: Pytest + Playwright + WireMock Standalone              │
│  - Database Teardown & Isolation Fixtures (`conftest.py`)              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 4. TEST DATA MANAGEMENT & STATE ISOLATION (TDM)

Test independence is guaranteed at every level to prevent test order dependency and flakiness:

1. **Deterministic Seed Personas (`DEC-001`):**
   - `admin@juice-sh.op` (Admin rights, access control tests)
   - `jim@juice-sh.op` (Seeded wallet balance $100.00, positive checkout)
   - `bender@juice-sh.op` (Seeded balance $0.00, negative balance checks)
2. **Dynamic Runtime Isolation (`DEC-003`):**
   - For all user creation, registration, and profile modification tests, dynamic email addresses and identities are generated using UUID prefixes:
     ```python
     f"test_{uuid.uuid4().hex[:8]}@juice-sh.op"
     ```
3. **Automated Database Teardown Fixture (`isolate_wallet_state`):**
   - Pytest autouse/session fixtures connect directly to SQLite/Sequelize via DB wrappers to snapshot and restore wallet balances and remove transient user rows after test execution.
4. **Mocking & Fault Injection (`DEC-012`):**
   - External services (fraud detection, third-party payment rails) run against **WireMock Standalone** on port `8088`. WireMock provides fault-injection (HTTP 503 Service Unavailable, HTTP 429 Rate Limiting, 5-second simulated latency) to test circuit breakers without touching real external APIs.

---

## 5. THE 8-STAGE AUTONOMOUS LIFECYCLE (END-TO-END WALKTHROUGH)

The canonical example used throughout the platform is User Story **`JS-39`** («Регистрация и профиль пользователя»), decomposed into Tasks **`JS-40`** (REST API), **`JS-41`** (Frontend UI), and **`JS-42`** (End-to-End User Journey).

### Stage 0: Health Gate (Pre-flight Validation)
- Before consuming LLM tokens, n8n polls 7 critical subsystem endpoints with 3-second timeouts:
  1. SUT Juice Shop (`http://localhost:3000`)
  2. Jira Cloud API (`romeo-timony.atlassian.net`)
  3. Qase TMS API (`https://api.qase.io/v1`)
  4. Google Gemini API (`generativelanguage.googleapis.com`)
  5. Telegram Bot API
  6. WireMock Mock Server (`http://localhost:8088`)
  7. Local PostgreSQL / SQLite storage
- If any critical service fails, the ticket is parked with an explanatory incident report in Jira.

### Stage 1: Definition of Ready (DoR Gate)
- **Trigger:** Jira Webhook on issue creation or transition to «To Do».
- **Analysis:** Gemini Flash evaluates the ticket against INVEST criteria and C06 Error Contract requirements using prompt `prompts/dor_evaluation/v2.0_enterprise.md`.
- **Verdict & Threshold:** Minimum score $\ge 80\%$.
  - **$\ge 80\%$ (ACCEPT):** Automatic transition to status **`10046 («В работе» / In Progress)`**. In-place publication of `[Этап 1 из 8] DoR Отчет`.
  - **$< 80\%$ (REJECT):** Ticket stays in «To Do». A detailed rework report is published with missing boundary conditions. Product Owner can reply with clarifications in the Jira thread; daemon recalculates the delta (`qaops_delta_refine.py`) and passes the gate once updated.

### Stage 2: MindMap & Whimsical Visual Design
- Builds a 5-level hierarchical mindmap (`L1 Root -> L2 Domain -> L3 Feature -> L4 Test Technique -> L5 Expected Result & Priority`).
- Employs ISTQB techniques: Boundary Value Analysis (BVA), Equivalence Partitioning (EP), State Transition, Error Guessing, OWASP Top 10 A01–A03 injection attacks.
- Outputs structured text syntax ready for **Whimsical text-to-mindmap import (`Ctrl+Shift+V`)** and attaches the direct interactive board URL to Jira.

### Stage 3: BDD Test Scenarios & Qase TMS Synchronization
- Converts MindMap leaves into Given-When-Then Gherkin specifications and Allure steps (`@allure.step`).
- Enforces Testing Pyramid rules:
  - Backend (`JS-40`): 100% marked as `automation: "to-be-automated"`.
  - Frontend (`JS-41`): Smoke & P1 marked as `to-be-automated`; native OS dialogs and secondary styling marked as `manual`.
- Connects to Qase TMS (Suite #86), creates hierarchical folders, and assigns permanent IDs (`QASE-787` through `QASE-798` for API; `QASE-811` through `QASE-822` for UI).
- Runs 4-tier deduplication to prevent duplicate cases.

### Stage 4: Bidirectional Requirements Traceability Matrix (RTM)
- Posts Jira Report `[Этап 4 из 8] Матрица прослеживаемости (RTM)`.
- Connects every Acceptance Criterion (AC) to MindMap branches, Qase Test Case IDs, test layer, and automation priority. Guarantees 100% coverage before code generation starts.

### Stage 5: Quality Gate 1 (Human-in-the-Loop Test Design Approval)
- The pipeline pauses execution (`Wait Node` in n8n; status `WAITING` in PostgreSQL).
- Posts card `[Этап 5 из 8] Контроль 1: Подтверждение тест-кейсов` in Jira (`⏳ ОЖИДАЕТ СОГЛАСОВАНИЯ QA LEAD`).
- Dispatches interactive Telegram alert to QA Lead via `@QApower_bot`.
- **Approval:** QA Lead inspects test cases in Qase TMS and replies **`«ОК»`** directly in the Jira thread of comment #5.
- Daemon detects approval, updates Jira comment to `✅ ОДОБРЕНО QA LEAD`, and triggers test scaffolding.

### Test Code Scaffolding (Sandbox Staging)
- `scripts/scaffold_dynamic.py` generates enterprise-grade Pytest/Playwright source code.
- Placed into quarantine sandbox: `tests/review/backend/test_js40_api.py` or `tests/review/frontend/test_js41_ui.py`.
- Enforces `DEC-004` (visual banners `# =============================================================================` and AAA steps) and `DEC-005` (direct method naming `test_tc{QASE_ID}_{name}`).

### Stage 6: Quality Gate 2 (Two-Phase Code Gate)
- **Phase 1 (Deterministic Static Gate - Seam 3):**
  - `ast.parse` validates syntax tree without code execution.
  - `ruff` checks blocking rules `E9, F63, F7, F82` (zero tolerance for undefined variables or broken imports).
  - `pytest --collect-only` executed in isolated environment. Syntax Collect Validity must be **100%**.
- **Phase 2 (Semantic LLM Code Reviewer):**
  - Gemini Flash evaluates code using `prompts/code_review_audit/v2.0_enterprise.md`.
  - Checks for Page Object Model adherence, absence of `time.sleep()`, presence of Pydantic response models, and Qase ID markers.
  - Generates audit log `tests/review/REVIEW_REPORT.md` (Score: 95/100).
- Posts Jira card `[Этап 6 из 8] Контроль 2 (Code Review)`. QA Lead approves via threaded reply `«ОК»`.

### Stage 7: Git Promotion & Worktree Isolation
- Daemon moves files from `tests/review/` to target locations (`tests/backend/test_js40_api.py`, `tests/frontend/test_js41_ui.py`).
- Creates isolated Git worktree: `git worktree add -B qa/js-40 .worktrees/qa-js-40 qa/main`.
- Content Digest Guard computes file hash; duplicate pushes are blocked.
- Commits with DCO sign-off (`git commit -s`), pushes to `qa/js-40`, updates `main`, and unfreezes n8n.
- Jira comment `[Этап 7 из 8] Внедрение автотестов` published.

### Stage 8: CI/CD Execution, Allure Reporting & Release Decision
- Tests execute via Pytest against SUT (12 API tests finish in ~1.01s).
- Allure Report generated with request/response payloads, headers, timings, and screenshots.
- `qaops.metrics.release_quality` calculates Release Quality Index (RQI) and posts final Go/No-Go verdict.
- Jira automatically transitions to **`10048 («Автотесты пройдены»)`** via transition ID `31`.
- Telegram notification broadcasted with direct links to Allure, Qase, Jira, and GitHub.

---

## 6. ARCHITECTURE DECISION RECORDS (ADR)

| Decision ID | Title | Core Rationale & Rule |
| :--- | :--- | :--- |
| **`DEC-001`** | **Seeded Personas** | Static accounts (`admin`, `jim` $100, `bender` $0) for deterministic business role tests. |
| **`DEC-002`** | **Page Object Model (POM)** | Zero raw selectors in test bodies; all locators encapsulated inside Page Classes. |
| **`DEC-003`** | **Dynamic UUID Isolation** | Dynamic email/username generation via `uuid.uuid4().hex[:8]` to eliminate 409 Conflict collisions. |
| **`DEC-004`** | **AAA Banners & Steps** | Every test must include `# ===` section headers and atomic `@allure.step` Arrange/Act/Assert blocks. |
| **`DEC-005`** | **Direct Qase ID Naming** | Test function names must match `test_tc{QASE_ID}_{description}` with `@pytest.mark.qase(id=...)`. |
| **`DEC-006`** | **Anti-Flaky Zero Sleep** | Strict ban on `time.sleep()` and `page.wait_for_timeout()`. Rely solely on Playwright autowaiting. |
| **`DEC-007`** | **Two-Phase Code Gate** | Static linting (AST + Ruff) must pass 100% before any LLM review tokens are spent. |
| **`DEC-008`** | **Prompt-as-Code Registry** | All prompts stored in Git as Markdown; version switching via environment variables without redeploy. |
| **`DEC-009`** | **Langfuse Tracing** | Every LLM call logged with metadata (`prompt_version`, `model`, `tokens`, `latency`, `cost`). |
| **`DEC-010`** | **Threaded HITL Approvals** | Human approvals («ОК») must be threaded replies to specific Stage cards to prevent race conditions. |
| **`DEC-011`** | **Git Worktree Isolation** | Promotion of generated code happens in `.worktrees/` to prevent dirtying developer working copies. |
| **`DEC-012`** | **WireMock Fault Injection** | External dependencies and 503/429 chaos engineering handled via WireMock Standalone. |
| **`DEC-013`** | **Pydantic Response Schemas** | All API responses validated against strict Pydantic models for contract integrity. |
| **`DEC-014`** | **Idempotent Transitions** | All Jira status transitions protected by hash keys to prevent duplicate lifecycle jumps. |
| **`DEC-015`** | **Audit Trail Preservation** | `REVIEW_REPORT.md` is never deleted upon promotion; kept permanently in `tests/review/`. |

---

## 7. PROMPTOPS, LLM-AS-A-JUDGE & EVALUATION FRAMEWORK

### Prompt-as-Code Registry (`prompts/registry.py`)
Prompts are treated identically to production application code:
- Stored as versioned Markdown files under `prompts/<domain>/` (`v1.0_baseline.md`, `v2.0_enterprise.md`).
- Loaded and rendered via `PromptRegistry` class.
- Instant, zero-downtime rollback via `.env` overrides (e.g. `PROMPT_VERSION_DOR_EVALUATION=v1.0_baseline`).

### DeepEval vs Promptfoo vs Static Code Gate:
- **Promptfoo:** Offline CLI tool used during prompt engineering to benchmark prompt variations before committing to Git.
- **DeepEval (G-Eval):** Used in **Contour 2 (Seam 2: Test Design Gate)** for natural language evaluation:
  - `Groundedness >= 0.90`: verifies every test step is derived strictly from Acceptance Criteria (zero hallucinations).
  - `Coverage >= 0.85`: verifies all positive, negative, and boundary paths are addressed.
- **Static Code Gate (`qaops.code_gate`):** Used in **Stage 6 (Gate 2)** for Python code analysis. DeepEval is deliberately NOT used for Python source code; instead, AST, Ruff, and isolated Pytest collect are combined with an LLM Code Reviewer.

---

## 8. 4-TIER QASE TMS DEDUPLICATION & IDEMPOTENCY ENGINE

Implemented in [`scripts/qase_deduplicate_evaluator.py`](file:///d:/Desktop/Juice_shop/qa-automation/scripts/qase_deduplicate_evaluator.py):

1. **Exact Title Matching:** Whitespace and case-normalized comparison against existing Qase cases.
2. **Backend API Signature Matching:**
   - Extracts Regex Endpoint (`/api/...`, `/rest/...`), HTTP Method (`GET`, `POST`...), Status Code (`200`, `401`...).
   - Identifies Business Intent (`sql_injection`, `jwt_token_auth`, `change_password`...).
   - If Endpoint + Method + Intent match an existing case, candidate is rejected as a duplicate.
3. **Frontend UI Module & Check Matching:**
   - Maps UI components (`registration_page`, `login_page`, `address_book`).
   - Categorizes checks (`positive`, `negative`, `validation`).
   - Rejects if token similarity across action steps exceeds 65%.
4. **Global Semantic Similarity (Jaccard Index $\ge 85\%$):**
   - Strips stop-words, tokenizes action/expected result sets, computes $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$. Rejects if $\ge 0.85$.
5. **Runtime Housekeeping:** Automatically identifies and purges orphan suites and duplicate cases with higher IDs, keeping the earliest original ID.

---

## 9. STATIC CODE GATE & ANTI-FLAKINESS ENGINEERING

Generated tests adhere to zero-flakiness standards:
1. **Zero Sleep:** `time.sleep()` is flagged as a fatal error by Ruff and AST auditors.
2. **Playwright Auto-Waiting:** Tests rely exclusively on web assertions (`expect(locator).to_be_visible()`, `expect(locator).to_have_text()`).
3. **Pydantic Strict Typing:**
   ```python
   response = requests.post(f"{BASE_URL}/api/Users", json=payload)
   data = UserRegistrationResponse.model_validate(response.json())
   assert data.status == "success"
   ```
4. **Collect Validity = 100%:** Pytest discovers and collects 100% of test methods before execution.

---

## 10. OBSERVABILITY, RESILIENCE & FALLBACKS

1. **Langfuse Tracing:** All LLM calls wrap execution in `trace()` and `span()` contexts, capturing token usage and generation latency.
2. **PostgreSQL Event Store (`qa_pipeline_events`):** Every stage transition, evaluation score, and approval is written to a relational audit log.
3. **Circuit Breakers & Exponential Backoff:** External calls (Jira, Qase, Gemini) utilize `resilient_request()` with retries and exponential backoff.
4. **Deterministic Fallbacks:** If the Gemini API is unreachable or rate-limited during code review, a deterministic fallback heuristic scores the AST structure, ensuring the pipeline never deadlocks.

---

## 11. TOP-15 TRICKY INTERVIEW QUESTIONS & MASTER ANSWERS

### Q1: Why did you split the architecture into two contours instead of doing everything in n8n or everything in Python?
> **Answer:** *«Separation of concerns. n8n excels as a lightweight, cloud-based webhook orchestrator and API integrator with Jira and Telegram. However, running heavy Python compilers, Playwright headless browsers, AST parsing, and Git worktrees inside an n8n container creates severe resource bloat and stability issues. By using a dual-contour architecture, n8n handles event routing, while our Python daemon executes heavy testing workflows in an isolated runtime».*

### Q2: How do you prevent LLMs from generating duplicate or redundant test cases?
> **Answer:** *«We implement a 4-tier deduplication engine in `qase_deduplicate_evaluator.py`. Before tests are sent to Qase TMS, candidates are compared against existing cases via: 1) normalized title matching, 2) API endpoint/method/intent signature extraction, 3) UI component and validation type matching, and 4) Jaccard token similarity with an 85% threshold. This guarantees zero test suite bloat».*

### Q3: Why don't you use DeepEval for evaluating the generated autotest code?
> **Answer:** *«DeepEval and its G-Eval framework are NLP metrics designed to evaluate text against text (e.g. Groundedness and Faithfulness of test cases against Acceptance Criteria). Source code requires AST validation, linter compliance (Ruff), and execution collection (Pytest). Therefore, we use DeepEval in Seam 2 for test design, and use our two-phase Static Code Gate + LLM Architecture Auditor for source code».*

### Q4: How do you guarantee that tests don't fail due to database pollution?
> **Answer:** *«We combine seeded static personas (`DEC-001`) for read-only scenarios with dynamic UUID generation (`DEC-003`) for mutating actions (registration, checkout). Additionally, Pytest autouse fixtures execute database rollback routines (`isolate_wallet_state`) that reset SQLite/Sequelize records after test completion».*

### Q5: What happens if an engineer rejects the test design at Quality Gate 1?
> **Answer:** *«The pipeline pauses. The ticket is held in Jira with the rejection remarks. The engineer or product owner can reply in the Jira comment thread with clarified requirements. The daemon picks up the reply, invokes `qaops_delta_refine.py` to recompute the delta, regenerates the MindMap and BDD cases, and republishes the card for re-evaluation».*

### Q6: Why did you choose WireMock instead of built-in mocking like `unittest.mock`?
> **Answer:** *«`unittest.mock` operates in-process and cannot test real network latency, connection resets, or HTTP proxies. WireMock Standalone runs as an independent mock server over HTTP (`DEC-012`), allowing us to test real network requests, 503 service outages, and 429 rate-limiting scenarios identically to real production microservices».*

### Q7: How do you prevent race conditions when multiple comments are added to a Jira ticket?
> **Answer:** *«We enforce Threaded Comment Approvals (`DEC-010`). The daemon ignores general top-level comments and strictly looks for replies in the thread of the specific Stage card (`stage_comment.id`). Furthermore, every comment ID is tracked in a processed set with database transaction locks».*

### Q8: What is your strategy for Prompt Versioning and Rollbacks?
> **Answer:** *«Prompt-as-Code via `prompts/registry.py`. Prompts are stored in Git under domain folders with semantic versioning (`v1.0_baseline.md`, `v2.0_enterprise.md`). Active versions are controlled via environment variables (`PROMPT_VERSION_*`), enabling instantaneous rollbacks without code redeployment or downtime».*

### Q9: How is the Testing Pyramid enforced in your test generation?
> **Answer:** *«In `08_format_testcases.js` and `scaffold_dynamic.py`, we apply layer-specific tagging: 100% of Backend API cases are marked `to-be-automated` because they are fast and cheap. For Frontend UI, only critical Smoke, Authentication, and Happy Path flows are automated; complex native OS dialogs and secondary visual checks are flagged as `manual` to prevent fragile UI suites».*

### Q10: How do you ensure the generated tests don't suffer from flakiness?
> **Answer:** *«We enforce `DEC-006`: an absolute ban on `time.sleep()` and arbitrary timeouts, verified via AST parsing and Ruff. All UI tests use Playwright's native auto-waiting and web assertions (`expect(locator).to_be_visible()`). Backend tests validate responses against strict Pydantic schemas».*

### Q11: How do you isolate Git operations when pushing newly generated tests?
> **Answer:** *«We use Git Worktrees (`DEC-011`). The daemon creates an isolated worktree at `.worktrees/qa-{issue_key}` branched from `qa/main`. It stages files, verifies content hashes with an idempotency guard, signs the commit (`-s`), pushes to the remote, and cleans up the worktree without ever dirtying the active working directory».*

### Q12: What metrics do you track for release confidence?
> **Answer:** *«We compute the Release Quality Index (RQI) in `qaops/metrics.py`. It aggregates DoR INVEST Score ($\ge 80\%$), Test Design Integrity ($\ge 90\%$), Syntax Collect Validity (100%), and Pytest Pass Rate (100%). If all criteria are met, an automated 'GO TO PRODUCTION' recommendation is logged».*

### Q13: How does the system handle Gemini API rate limits or outages?
> **Answer:** *«All LLM calls use `resilient_request` with exponential backoff and retries. If the API is completely exhausted, the system falls back to a deterministic heuristic auditor (`deterministic_fallback`) that evaluates AST structure and regex markers, preventing pipeline deadlock».*

### Q14: How are tests linked back to Jira and Qase TMS in the source code?
> **Answer:** *«Through `DEC-005`: every test method is named `test_tc{QASE_ID}_{description}` and decorated with `@pytest.mark.qase(id=...)` and Allure decorators. When tests run, Allure and Qase reporters map execution results directly to test cases in Qase TMS and tickets in Jira».*

### Q15: Why is OWASP Juice Shop an ideal testbed for this platform?
> **Answer:** *«Juice Shop features a modern architecture (Angular SPA + Node/Express REST + SQLite/Sequelize) alongside real-world security challenges (SQLi, broken auth, rate limits, file uploads). This allows us to validate not only positive happy-paths, but also complex boundary, security (OWASP A01–A03), and contract validation scenarios».*
