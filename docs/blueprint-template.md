# Day 13 Observability Lab Report

> **Instruction**: Fill in all sections below. This report is designed to be parsed by an automated grading assistant. Ensure all tags (e.g., `[GROUP_NAME]`) are preserved.

## 1. Team Metadata
- [GROUP_NAME]: A20-Observability-Lab
- [REPO_URL]: https://github.com/trinhketien/2A202600500_TrinhKeTien_Lab13-Observability.git
- [MEMBERS]:
  - Member A: Trịnh Kế Tiến (2A202600500) | Role: Correlation ID & Middleware
  - Member B: Vũ Hoàng Minh (2A202600440) | Role: PII Scrubbing & Privacy
  - Member C: Phạm Văn Thành (2A202600272) | Role: Dashboard & Metrics
  - Member D: Nguyễn Thành Luân (2A202600204) | Role: Alerts, SLO & Runbooks
  - Member E: Thái Tuấn Khang (2A202600289) | Role: Tracing, Testing & Report

---

## 2. Group Performance (Auto-Verified)
- [VALIDATE_LOGS_FINAL_SCORE]: 100/100
- [TOTAL_TRACES_COUNT]: 35+ (15 REST API + 20 via app)
- [PII_LEAKS_FOUND]: 0

---

## 3. Technical Evidence (Group)

### 3.1 Logging & Tracing
- [EVIDENCE_CORRELATION_ID_SCREENSHOT]: Tất cả logs chứa `req-<8hex>` unique
  - Xem: `docs/screenshots/04_pii_redacted_logs.txt`
- [EVIDENCE_PII_REDACTION_SCREENSHOT]: Verified:
  - `student@vinuni.edu.vn` → `[REDACTED_EMAIL]`
  - `0987654321` → `[REDACTED_PHONE_VN]`
  - `4111 1111 1111 1111` → `[REDACTED_CREDIT_CARD]`
  - `012345678901` → `[REDACTED_CCCD]`
  - `B12345678` → `[REDACTED_PASSPORT]`
  - Xem: `docs/screenshots/04_pii_redacted_logs.txt`
- [EVIDENCE_TRACE_WATERFALL_SCREENSHOT]: 20+ traces hiện trên Langfuse self-hosted (localhost:3000)
  - Xem: `docs/screenshots/01_traces_list.png`
  - Xem: `docs/screenshots/02_trace_detail.png`
- [TRACE_WATERFALL_EXPLANATION]: Mỗi trace ghi nhận pipeline: request → PII scrub → RAG retrieval → LLM generation → response. Decorator `@observe()` trên `LabAgent.run()` tạo parent span, metadata gồm doc_count, query_preview, token usage.

### 3.2 Dashboard & SLOs
- [DASHBOARD_6_PANELS_SCREENSHOT]: `dashboard.html` — 6 panels Chart.js:
  - Xem: `docs/screenshots/03_langfuse_dashboard.png`
  - Xem: `docs/screenshots/07_langfuse_full_dashboard.png` ← Langfuse Dashboard: **20 Traces tracked**, biểu đồ traces theo thời gian (4/19-4/20/2026)
  1. **Latency P50/P95/P99** (line chart, SLO threshold 3000ms)
  2. **Traffic count** (line chart, request volume)
  3. **Error rate + breakdown** (doughnut chart)
  4. **Cost over time** (line chart, budget line $2.50)
  5. **Tokens In/Out** (bar chart)
  6. **Quality proxy score** (line chart, SLO 0.75)
- [SLO_TABLE]:

| SLI | Target | Window | Current Value |
|---|---:|---|---:|
| Latency P95 | < 3000ms | 28d | 2651ms ✅ |
| Error Rate | < 2% | 28d | 0.0% ✅ |
| Cost Budget | < $2.5/day | 1d | $0.0605 ✅ |
| Quality Avg | ≥ 0.75 | 28d | 0.88 ✅ |

### 3.3 Alerts & Runbook
- [ALERT_RULES_SCREENSHOT]: 5 alert rules trong `config/alert_rules.yaml`
  1. `high_latency_p95` (P2) — threshold 5000ms for 30m
  2. `high_error_rate` (P1) — threshold 5% for 15m
  3. `cost_budget_spike` (P2) — threshold $2.5 for 1d
  4. `quality_score_drop` (P2) — threshold 0.65 for 1h
  5. `token_budget_exceeded` (P3) — threshold 100000 for 1d
- [SAMPLE_RUNBOOK_LINK]: docs/alerts.md

---

## 4. Incident Response (Group)
- [SCENARIO_NAME]: rag_slow
- [SYMPTOMS_OBSERVED]:
  - Latency tăng từ ~460ms baseline lên ~2654ms (5.8x increase)
  - P95 latency vượt SLO threshold
  - Tất cả requests vẫn trả 200 OK nhưng tail latency gây suy giảm UX
- [ROOT_CAUSE_PROVED_BY]:
  - Metrics endpoint: `latency_p95: 2651ms` (vs ~150ms baseline)
  - Log timestamps: mỗi request mất ~2654ms trong thời gian incident
  - Incident toggle `rag_slow` confirmed enabled via `/health`
  - Flow: Metrics (P95 spike) → Traces (RAG span chậm) → Logs (correlation ID xác định request cụ thể)
- [FIX_ACTION]:
  - Disable incident toggle via `POST /incidents/rag_slow/disable`
  - RAG retrieval latency quay lại normal
  - Post-fix: requests trở lại ~460ms
- [PREVENTIVE_MEASURE]:
  - Alert rule `high_latency_p95` tự động phát hiện
  - Runbook hướng dẫn check RAG span vs LLM span
  - Long-term: circuit breaker cho RAG, fallback cached results

---

## 5. Individual Reports

---

### 5.1 Trịnh Kế Tiến (2A202600500) — Correlation ID & Middleware

**Phần việc đảm nhận:**
- Thiết kế và implement `CorrelationIdMiddleware` trong `app/middleware.py`
- Cấu hình log enrichment trong `app/main.py` (endpoint `/chat`)
- Thêm `load_dotenv()` vào `main.py` để load `.env` trước khi import modules

**Chi tiết kỹ thuật:**

1. **Correlation ID Generation**: Tạo ID dạng `req-<8-char-hex>` bằng `uuid.uuid4().hex[:8]`. UUID4 đảm bảo uniqueness trên distributed systems mà không cần central coordinator.

2. **Context Management**: Sử dụng `structlog.contextvars` để:
   - `clear_contextvars()` đầu mỗi request → tránh context leakage giữa requests
   - `bind_contextvars(correlation_id=cid)` → mọi log trong request tự động có ID

3. **Response Headers**: Thêm `x-request-id` (correlation ID) và `x-response-time-ms` vào response → client có thể trace lại request khi report bug.

4. **Log Enrichment**: Trong `/chat` endpoint, bind thêm 5 context fields:
   - `user_id_hash`: SHA-256 truncated 12 chars (không lưu plaintext user ID)
   - `session_id`: Grouping requests cùng phiên
   - `feature`: Loại tính năng (qa/summary)
   - `model`: Model LLM đang dùng
   - `env`: Môi trường (dev/staging/prod)

**Bài học rút ra:**
- `contextvars` là cách thread-safe để truyền context trong async Python, không cần truyền tham số qua từng hàm.
- Correlation ID phải được clear đầu request để tránh "context pollution" — một request nhận ID của request trước.

**Evidence**: Commits trong `app/middleware.py`, `app/main.py`

---

### 5.2 Vũ Hoàng Minh (2A202600440) — PII Scrubbing & Privacy

**Phần việc đảm nhận:**
- Mở rộng PII regex patterns trong `app/pii.py`
- Kích hoạt PII scrubbing processor trong `app/logging_config.py`
- Viết test cases cho PII trong `tests/test_pii.py`

**Chi tiết kỹ thuật:**

1. **PII Regex Patterns**: Xây dựng 6 patterns:
   - `email`: `[\w\.-]+@[\w\.-]+\.\w+` — match mọi dạng email
   - `credit_card`: `\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b` — 16 digits, có/không separator
   - `cccd`: `\b\d{12}\b` — CCCD/CMND Việt Nam 12 số
   - `phone_vn`: `(?:\+84|0)[ \.-]?\d{3}[ \.-]?\d{3}[ \.-]?\d{3,4}` — SĐT VN
   - `passport`: `\b[A-Z]\d{7,8}\b` — Hộ chiếu format quốc tế
   - `vn_address`: `(?:số\s+\d+|đường\s+\S+|...)` — Địa chỉ Việt Nam

2. **Regex Ordering Bug & Fix**: Phát hiện CCCD 12 chữ số (`012345678901`) bị phone regex match trước (vì bắt đầu bằng `0`). Fix: đặt `credit_card` → `cccd` trước `phone_vn` trong dict để longer patterns match trước.

3. **Structlog Processor**: Kích hoạt `scrub_event` processor trong pipeline — tự động scan mọi string value trong log event và thay thế PII bằng `[REDACTED_*]`.

4. **Testing**: 12 test cases phủ tất cả patterns, edge cases (multiple PII, clean text), hash determinism, và summarize function.

**Bài học rút ra:**
- Thứ tự regex quan trọng khi patterns overlap — luôn đặt specific/longer patterns trước generic/shorter ones.
- PII scrubbing nên ở cuối structlog pipeline, trước renderer, để catch mọi data.

**Evidence**: Commits trong `app/pii.py`, `app/logging_config.py`, `tests/test_pii.py`

---

### 5.3 Phạm Văn Thành (2A202600272) — Dashboard & Metrics Visualization

**Phần việc đảm nhận:**
- Thiết kế và xây dựng `dashboard.html` — real-time monitoring dashboard
- Cấu hình Chart.js cho 6 panels theo spec `docs/dashboard-spec.md`
- Tích hợp auto-refresh và SLO threshold lines

**Chi tiết kỹ thuật:**

1. **Technology Stack**: HTML + CSS + Chart.js CDN — không cần build tool, mở trực tiếp trong browser. Dark theme cho professional look.

2. **6 Panels Implementation**:
   - **Panel 1 - Latency**: Line chart P50/P95/P99 với SLO line tại 3000ms (màu đỏ dashed)
   - **Panel 2 - Traffic**: Line chart request count, border gradient xanh
   - **Panel 3 - Error Rate**: Doughnut chart phân loại lỗi (timeout, validation, internal)
   - **Panel 4 - Cost**: Line chart tổng cost USD, budget line tại $2.50
   - **Panel 5 - Tokens**: Stacked bar chart In/Out tokens — giúp theo dõi usage
   - **Panel 6 - Quality**: Line chart quality score, SLO line tại 0.75

3. **Auto-refresh**: `setInterval(fetchMetrics, 15000)` — poll `/metrics` mỗi 15s, cập nhật data + chart animation smooth.

4. **SLO Banner**: Header hiển thị trạng thái 4 SLO với indicator xanh/đỏ real-time.

**Bài học rút ra:**
- Dashboard nên hiển thị SLO thresholds trực tiếp trên chart (không riêng bảng) để operator phát hiện vi phạm ngay bằng mắt.
- Auto-refresh 15s là cân bằng giữa real-time và tải server.

**Evidence**: File `dashboard.html`, demo live

---

### 5.4 Nguyễn Thành Luân (2A202600204) — Alerts, SLO & Runbooks

**Phần việc đảm nhận:**
- Thiết kế 5 alert rules trong `config/alert_rules.yaml`
- Cấu hình SLO targets trong `config/slo.yaml`
- Viết runbooks chi tiết trong `docs/alerts.md`

**Chi tiết kỹ thuật:**

1. **5 Alert Rules**:

| Rule | Severity | Condition | Window |
|---|---|---|---|
| `high_latency_p95` | P2 | P95 > 5000ms | 30m |
| `high_error_rate` | P1 | Error > 5% | 15m |
| `cost_budget_spike` | P2 | Cost > $2.5 | 1d |
| `quality_score_drop` | P2 | Quality < 0.65 | 1h |
| `token_budget_exceeded` | P3 | Tokens > 100k | 1d |

2. **Severity Design**: P1 = immediate (page on-call), P2 = urgent (Slack alert), P3 = informational (email). Mỗi rule có `for` window để tránh false positive từ transient spikes.

3. **SLO Configuration**: 4 SLO targets với 28-day rolling window (phù hợp sprint cycle). Mỗi SLO có `notes` mô tả rationale.

4. **Runbook Structure**: Mỗi alert có 5 phần:
   - Description → khi nào trigger
   - Impact → ảnh hưởng user
   - Investigation → step-by-step debug
   - Remediation → hành động fix
   - Prevention → long-term improvement

**Bài học rút ra:**
- Alert fatigue là vấn đề thực tế — cần `for` window và severity phân tầng rõ ràng.
- Runbook phải actionable (có command cụ thể), không chỉ mô tả chung chung.

**Evidence**: Commits trong `config/alert_rules.yaml`, `config/slo.yaml`, `docs/alerts.md`

---

### 5.5 Thái Tuấn Khang (2A202600289) — Tracing, Testing & Integration

**Phần việc đảm nhận:**
- Fix Langfuse v3.2.1 tracing adapter trong `app/tracing.py`
- Viết test middleware trong `tests/test_middleware.py`
- Chạy load test, incident injection, và validation
- Tổng hợp báo cáo nhóm

**Chi tiết kỹ thuật:**

1. **Langfuse v3 Migration**: SDK v3.2.1 thay đổi hoàn toàn API:
   - Import: `from langfuse import observe, get_client` (thay vì `langfuse.decorators`)
   - Context: `get_client().update_current_trace()` (thay vì `langfuse_context`)
   - `update_current_span()` không hỗ trợ `usage_details` → merge vào `metadata`
   - Adapter class `_LangfuseContext` wrap API mới, giữ interface cũ cho `agent.py`

2. **Testing Strategy**:
   - `test_middleware.py`: 2 tests verify correlation ID format (`req-XXXXXXXX`) và uniqueness (100 IDs, 0 collisions)
   - `test_metrics.py`: Percentile calculation (có sẵn)
   - Tổng: 15/15 tests passed

3. **Load Testing & Validation**:
   - 3 batches × 10 requests = 30 requests, 100% success rate
   - Incident injection `rag_slow`: latency 460ms → 2654ms → 460ms
   - `validate_logs.py`: 100/100 (4/4 checks PASSED)

4. **REST API Trace Ingestion**: Khi decorator-based tracing gặp delay, sử dụng REST API `/api/public/ingestion` để gửi 15 traces trực tiếp → 15/15 status 201 Created.

**Bài học rút ra:**
- SDK major version changes có thể break import paths hoàn toàn — luôn check `dir(module)` trước khi assume API.
- `try/except` fallback pattern trong `tracing.py` là excellent practice — app chạy bình thường ngay cả khi tracing service down.

**Evidence**: Commits trong `app/tracing.py`, `tests/test_middleware.py`, load_test output

---

## 6. Bonus Items
- [BONUS_DASHBOARD]: Dashboard dark theme, Chart.js animations, SLO threshold lines, auto-refresh 15s (+3đ)
- [BONUS_AUDIT_LOGS]: Audit log path tách riêng tại `data/audit.jsonl` (+2đ)
- [BONUS_CUSTOM_METRIC]: Quality score proxy metric với heuristic scoring (+2đ)
