# Lab 13 — Bộ Câu Hỏi & Trả Lời Chuẩn Bị Demo

> Tài liệu này giúp cả nhóm chuẩn bị trả lời câu hỏi giảng viên khi demo.

---

## 👤 TV1 (Trịnh Kế Tiên) — Correlation ID & Middleware

### Q1: Correlation ID tạo như nào?
**A:** Dùng `uuid.uuid4().hex[:8]` lấy 8 ký tự hex ngẫu nhiên, ghép với prefix `req-` → tạo ra dạng `req-a1b2c3d4`. UUID4 dùng random bytes nên đảm bảo unique mà không cần database hay counter trung tâm. Xác suất trùng lặp với 8 hex chars là 1/4.3 tỷ, đủ cho một session.

### Q2: Tại sao phải clear contextvars đầu mỗi request?
**A:** Vì `contextvars` lưu trữ theo async context. Nếu không clear, request mới có thể "thừa kế" context của request cũ — ví dụ request B sẽ mang correlation_id của request A → logs bị lẫn, debug sai hoàn toàn. `clear_contextvars()` đầu middleware đảm bảo mỗi request bắt đầu với context sạch.

### Q3: Response headers `x-request-id` dùng để làm gì?
**A:** Khi user report bug, họ chỉ cần gửi giá trị `x-request-id` từ response header → team dev dùng ID đó grep trong logs để tìm chính xác request lỗi trong hàng triệu dòng log. Không cần hỏi user thêm bất kỳ thông tin nào.

### Q4: `bind_contextvars` khác `log.info(field=value)` chỗ nào?
**A:** `bind_contextvars` gắn field vào **tất cả** log entries trong request đó (tự động), không cần truyền parameter. `log.info(field=value)` chỉ gắn vào **1 dòng log cụ thể**. Dùng bind cho thông tin xuyên suốt (user_id, session_id), dùng inline cho thông tin cục bộ (latency_ms).

### Q5: Tại sao hash user_id thay vì lưu plaintext?
**A:** GDPR/Privacy — log file thường lưu lâu dài, nếu bị leak sẽ lộ danh tính user. SHA-256 hash là one-way: vẫn nhóm được logs cùng user (hash giống nhau) nhưng không thể suy ngược ra user thật.

---

## 👤 TV2 — PII Scrubbing & Privacy

### Q1: Regex CCCD vs Phone bị conflict như nào? Fix thế nào?
**A:** CCCD là 12 chữ số (`\b\d{12}\b`), Phone VN bắt đầu bằng `0` + 9-10 số (`(?:\+84|0)\d{3}\d{3}\d{3,4}`). Khi CCCD là `012345678901`, phone regex match trước vì nó đứng trước trong dict → CCCD bị nhận nhầm là phone.

**Fix:** Đổi thứ tự: `credit_card` → `cccd` → `phone_vn`. Pattern dài/cụ thể đặt trước pattern ngắn/tổng quát. Đây là nguyên tắc "longest match first" trong regex engineering.

### Q2: PII scrubbing ở đâu trong structlog pipeline?
**A:** Ở `scrub_event` processor, đặt **trước** JSON renderer nhưng **sau** các processor khác (timestamper, add_log_level). Flow:
```
Log data → timestamper → add_log_level → scrub_event → JSONRenderer → file
```
Lý do: scrub phải chạy sau khi tất cả data đã được thêm vào event (để không bỏ sót), nhưng trước khi render ra file (để PII không bao giờ chạm disk).

### Q3: Tại sao dùng `[REDACTED_EMAIL]` thay vì xóa hẳn?
**A:** Giữ placeholder giúp:
1. Debug biết "ở đây có email" → hiểu context
2. Đếm được bao nhiêu PII bị redact (metrics)
3. Audit compliance — chứng minh "có PII nhưng đã được xử lý"

Nếu xóa hẳn → mất context, không biết field đó có data hay trống.

### Q4: Regex có thể miss PII không? Làm sao cải thiện?
**A:** Có — regex là rule-based, không thể cover 100% biến thể. Ví dụ: email viết tắt `abc at gmail dot com`, phone có dấu cách lạ. Cải thiện bằng:
1. Thêm patterns khi phát hiện case mới
2. Dùng NER (Named Entity Recognition) model cho accuracy cao hơn
3. Kết hợp: regex cho patterns rõ ràng + ML model cho edge cases

### Q5: Test PII như nào để đảm bảo không leak?
**A:** 12 test cases phủ 6 pattern types + edge cases:
- Mỗi pattern: verify text gốc biến mất, placeholder xuất hiện
- Multiple PII: text có cả email + phone + card → tất cả bị redacted
- Clean text: text không chứa PII → giữ nguyên (tránh false positive)
- Hash determinism: cùng input → cùng hash (consistency)

---

## 👤 TV3 — Dashboard & Metrics

### Q1: 6 panels là gì? Tại sao chọn 6 cái này?
**A:** Theo mô hình **RED + USE** trong observability:
1. **Latency P50/P95/P99** — tốc độ phản hồi (user experience)
2. **Traffic** — lưu lượng request (capacity planning)
3. **Error Rate** — tỷ lệ lỗi (reliability)
4. **Cost** — chi phí token/API (business metric)
5. **Tokens In/Out** — lượng token tiêu thụ (resource usage)
6. **Quality Score** — chất lượng output (business value)

Panels 1-3 = RED metrics (Rate, Error, Duration), panel 5 = USE metrics (Utilization), panels 4+6 = business KPIs.

### Q2: SLO line trên chart có ý nghĩa gì?
**A:** SLO line (đường ngang đỏ) là **ngưỡng cam kết** — ví dụ Latency P95 < 3000ms. Khi metric vượt qua line → vi phạm SLO → cần hành động. Vẽ trực tiếp trên chart giúp operator phát hiện **bằng mắt** trong 1 giây, không cần đọc số.

### Q3: Auto-refresh 15 giây, tại sao không 1 giây?
**A:** Cân bằng giữa:
- **Real-time**: Refresh nhanh hơn → phát hiện sự cố sớm hơn
- **Performance**: Mỗi refresh = 1 HTTP request đến `/metrics` → refresh 1s = 60 req/phút, gây tải server
- **15s** là standard trong industry (Grafana default cũng 15s). Đủ nhanh phát hiện incident (trễ tối đa 15s) mà không gây overhead.

### Q4: P50, P95, P99 khác nhau thế nào? Tại sao cần P99?
**A:**
- **P50** (median): 50% requests nhanh hơn giá trị này → "user bình thường"
- **P95**: 95% requests nhanh hơn → "hầu hết users"
- **P99**: 99% requests nhanh hơn → "worst case users"

Cần P99 vì: nếu 1% users bị chậm 10x, P50 và P95 không phản ánh được. Nhưng 1% của 1 triệu users = 10,000 người bị ảnh hưởng. P99 bắt tail latency mà average/median che giấu.

### Q5: Dashboard dùng Chart.js — production nên dùng gì?
**A:** Lab dùng Chart.js (CDN, đơn giản) là đủ. Production nên dùng:
- **Grafana** — thiết kế cho observability, có alerting built-in
- **Datadog/New Relic** — managed service, không cần tự host
- Lý do: Chart.js không có persistence, alerting, annotation, multi-user — chỉ phù hợp prototype.

---

## 👤 TV4 — Alerts, SLO & Runbooks

### Q1: Tại sao cần `for` window trong alert rule?
**A:** Tránh **false positive** (chuông báo giả). Ví dụ: latency spike 1 giây do GC pause → nếu không có `for: 30m`, alert fire ngay → team bị làm phiền vô ích.

`for: 30m` nghĩa là: metric phải vi phạm **liên tục 30 phút** mới trigger alert → chỉ fire khi có vấn đề thực sự, không phải transient spike.

### Q2: P1 vs P2 vs P3 khác nhau thế nào?
**A:**
| Severity | Nghĩa | Hành Động | Ví dụ |
|---|---|---|---|
| **P1** | Critical — user bị ảnh hưởng ngay | Page on-call 24/7, fix trong 15 phút | Error rate > 5% |
| **P2** | Urgent — user có thể bị ảnh hưởng sớm | Slack alert, fix trong 1-4 giờ | Latency P95 cao |
| **P3** | Info — không ảnh hưởng user hiện tại | Email, review next business day | Token budget gần hết |

Phân tầng giúp tránh **alert fatigue** — nếu mọi alert đều P1, team sẽ bỏ qua tất cả.

### Q3: Runbook cần những gì? Tại sao quan trọng?
**A:** Runbook cần 5 phần: Description, Impact, Investigation (step-by-step), Remediation (fix), Prevention (long-term). Quan trọng vì:
- On-call lúc 3AM đầu óc không tỉnh táo → cần hướng dẫn cụ thể
- Giảm **MTTR** (Mean Time To Resolve) — có sẵn command chạy, không cần nghĩ
- Knowledge transfer — người mới cũng handle được incident

### Q4: SLO target đặt như nào cho hợp lý?
**A:** Dựa trên **user expectation + business need**:
- Latency P95 < 3000ms: User chờ tối đa 3s cho AI response là chấp nhận được
- Error < 2%: 98% requests thành công → standard cho non-critical service  
- Cost < $2.5/day: Budget constraint → business decides
- Quality ≥ 0.75: 75% quality score → đảm bảo response hữu ích

**Không nên** đặt SLO = 100% → không thực tế, tốn chi phí vô hạn. Google khuyến nghị 99.9% cho hầu hết services.

### Q5: 5 alert rules cover những risk nào?
**A:**
1. `high_latency_p95` → **Performance degradation** (RAG chậm, LLM chậm)
2. `high_error_rate` → **System failure** (service down, bug)
3. `cost_budget_spike` → **Financial risk** (prompt injection tốn token)
4. `quality_score_drop` → **Quality degradation** (model hallucination)
5. `token_budget_exceeded` → **Resource exhaustion** (abuse, DDoS)

Cover cả 3 trụ: **Reliability** (1,2), **Cost** (3,5), **Quality** (4).

---

## 👤 TV5 — Tracing, Testing & Integration

### Q1: Langfuse v3 khác v2 chỗ nào?
**A:** Thay đổi lớn nhất:
| | v2 | v3.2.1 |
|---|---|---|
| Import | `from langfuse.decorators import observe` | `from langfuse import observe` |
| Context | `langfuse_context.update_current_trace()` | `get_client().update_current_trace()` |
| Transport | REST API `/api/public/ingestion` | OpenTelemetry `/api/public/otel/v1/traces` |
| Span update | `usage_details` parameter | Không hỗ trợ → merge vào `metadata` |

SDK v3 chuyển sang **OTEL-native** → compatible với OpenTelemetry ecosystem nhưng breaking change cho code cũ.

### Q2: Fallback decorator hoạt động ra sao?
**A:** File `tracing.py` dùng pattern:
```python
try:
    from langfuse import observe, get_client  # Real tracing
except Exception:
    def observe(*args, **kwargs):             # Dummy - no-op
        def decorator(func): return func
        return decorator
```
Nếu Langfuse SDK không cài hoặc lỗi → fallback sang dummy decorator `@observe()` mà **không thay đổi logic app**. App chạy bình thường, chỉ mất tracing. Đây là **graceful degradation** pattern.

### Q3: Load test phát hiện được gì?
**A:** 3 batches × 10 requests = 30 total:
- **Batch 1** (concurrency 5): Phát hiện latency tăng khi concurrent → bottleneck
- **Incident injection** (rag_slow): Latency tăng từ 460ms → 2654ms → confirm alert rule detect được
- **Post-fix batch**: Latency về 460ms → confirm fix worked

Cũng verify: PII redaction under load, correlation ID uniqueness, log schema consistency.

### Q4: Incident response flow: Metrics → Traces → Logs?
**A:** Đây là flow debug **top-down**:
1. **Metrics**: Dashboard panel 1 → thấy P95 spike lên 2654ms → "có vấn đề"
2. **Traces**: Mở Langfuse trace → thấy RAG span chiếm 2500ms (bình thường 0ms) → "RAG là bottleneck"
3. **Logs**: Grep correlation ID → thấy `incident_enabled: rag_slow` → "root cause: incident toggle"

Mỗi layer zoom in sâu hơn: Metrics (what), Traces (where), Logs (why).

### Q5: Test strategy — tại sao 15 tests là đủ?
**A:** Coverage theo risk:
- **PII (12 tests)**: Highest risk — leak PII = legal issue → test mọi pattern + edge cases
- **Middleware (2 tests)**: Format correctness + uniqueness → 2 tests cover core contract
- **Metrics (1 test)**: Percentile math — 1 test verify algorithm đúng

Principle: **Test density tỷ lệ với risk level**. PII cần nhiều test nhất vì hậu quả nghiêm trọng nhất.

---

## 🔥 Câu Hỏi Chung (Ai Cũng Phải Biết)

### Q: Ba trụ cột Observability là gì?
**A:** **Metrics** (số liệu tổng hợp — latency, error rate), **Traces** (hành trình request qua system), **Logs** (chi tiết sự kiện cụ thể). Ba cái bổ sung nhau: Metrics phát hiện "có vấn đề", Traces chỉ ra "ở đâu", Logs cho biết "tại sao".

### Q: Observability khác Monitoring thế nào?
**A:** **Monitoring** = bạn biết trước cần đo gì → đặt alert. **Observability** = system đủ data để debug vấn đề **chưa từng gặp** → không cần biết trước hỏi gì. Observability là superset của monitoring.

### Q: validate_logs.py check những gì?
**A:** 4 checks: (1) JSON schema đúng (service, event, level, ts), (2) Correlation ID present & unique, (3) Log enrichment (user_id_hash, session_id, feature, model, env), (4) PII scrubbing (không còn email/phone/card plaintext trong logs).
