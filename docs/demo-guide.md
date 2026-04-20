# Lab 13 — Hướng Dẫn Chạy Demo & Kết Quả Mong Đợi

## Bước 0: Kích hoạt môi trường
```powershell
cd d:\Antigravity\AI_thucchien\2_Co-so-ly-luan\Day-13
.\.venv\Scripts\Activate.ps1
```
> ⚠️ Là `.venv` (có dấu chấm), KHÔNG phải `venv`

---

## Bước 1: Khởi động server
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```
### Kết quả mong đợi:
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
{"service": "day13-observability-lab", "env": "dev", "payload": {"tracing_enabled": true}, "event": "app_started", ...}
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```
✅ Quan trọng: `"tracing_enabled": true` → Langfuse đã kết nối

---

## Bước 2: Gửi requests (MỞ TERMINAL MỚI)
```powershell
cd d:\Antigravity\AI_thucchien\2_Co-so-ly-luan\Day-13
.\.venv\Scripts\Activate.ps1
python scripts/load_test.py --concurrency 5
```
### Kết quả mong đợi:
```
[200] req-a1b2c3d4 | qa | 626.4ms
[200] req-e5f6a7b8 | summary | 459.7ms
[200] req-c9d0e1f2 | qa | 763.9ms
... (10 dòng, tất cả 200 OK)
```
✅ Mỗi dòng có: [200] = thành công, req-XXXXXXXX = correlation ID, qa/summary = feature

---

## Bước 3: Kiểm tra điểm (validate_logs)
```powershell
python scripts/validate_logs.py
```
### Kết quả mong đợi:
```
--- Lab Verification Results ---
Total log records analyzed: 21
Records with missing required fields: 0
Records with missing enrichment (context): 0
Unique correlation IDs found: 10
Potential PII leaks detected: 0

--- Grading Scorecard (Estimates) ---
+ [PASSED] Basic JSON schema
+ [PASSED] Correlation ID propagation
+ [PASSED] Log enrichment
+ [PASSED] PII scrubbing

Estimated Score: 100/100
```
✅ 4/4 PASSED, Score: 100/100

---

## Bước 4: Xem logs (PII redacted)
```powershell
Get-Content data/logs.jsonl | Select-String "REDACTED" | Select-Object -First 5
```
### Kết quả mong đợi:
```
... "message_preview": "What is your refund policy? My email is [REDACTED_EMAIL]" ...
... "message_preview": "Here is my phone [REDACTED_PHONE_VN], what should be logged?" ...
... "message_preview": "What is the policy for PII and credit card [REDACTED_CREDIT_CARD]?" ...
```
✅ Email, Phone, Credit Card đều bị redact → PII không bao giờ lưu plaintext

---

## Bước 5: Xem metrics
```powershell
python -c "import httpx; import json; r=httpx.get('http://127.0.0.1:8000/metrics'); print(json.dumps(r.json(), indent=2))"
```
### Kết quả mong đợi:
```json
{
  "traffic": 10,
  "latency_p50": 150.0,
  "latency_p95": 614.0,
  "latency_p99": 614.0,
  "avg_cost_usd": 0.002,
  "total_cost_usd": 0.02,
  "tokens_in_total": 340,
  "tokens_out_total": 1200,
  "error_breakdown": {},
  "quality_avg": 0.88
}
```
✅ Tất cả SLO đều trong ngưỡng: latency < 3000ms, error = 0%, quality > 0.75

---

## Bước 6: Inject incident (demo incident response)
```powershell
python scripts/inject_incident.py --scenario rag_slow
```
### Kết quả:
```
200 {'ok': True, 'incidents': {'rag_slow': True, 'tool_fail': False, 'cost_spike': False}}
```

Sau đó gửi thêm requests:
```powershell
python scripts/load_test.py --concurrency 1
```
### Kết quả (latency tăng 5-6x):
```
[200] req-xxx | qa | 2654.3ms    ← trước chỉ ~460ms
[200] req-xxx | qa | 2653.8ms
...
```
✅ Chứng minh: incident injection → latency spike → alert rule sẽ fire

Disable incident:
```powershell
python scripts/inject_incident.py --scenario rag_slow --disable
```
Gửi requests lại → latency về bình thường (~460ms).

---

## Bước 7: Xem Dashboard
Mở file trong browser:
```
d:\Antigravity\AI_thucchien\2_Co-so-ly-luan\Day-13\dashboard.html
```
### Kết quả: 6 panels hiện data real-time
1. Latency chart (có SLO line đỏ tại 3000ms)
2. Traffic count
3. Error rate (0%)
4. Cost (< $2.50 budget)
5. Tokens In/Out
6. Quality score (> 0.75 SLO)

---

## Bước 8: Xem Langfuse Traces
1. Mở browser → https://cloud.langfuse.com
2. Đăng nhập (trinhketiennic@gmail.com)
3. Chọn project **"Lab13-Observability 2"** (KHÔNG phải project 1)
4. Click tab **Traces**

### Kết quả mong đợi: ≥10 traces với:
- Name: `lab13-agent-run-*`
- User ID: hashed
- Tags: lab, qa, claude-sonnet-4-5
- Input/Output: query & answer

---

## Bước 9: Chạy tests
```powershell
python -m pytest tests/ -v
```
### Kết quả mong đợi:
```
tests/test_metrics.py::test_percentile_basic PASSED
tests/test_middleware.py::test_correlation_id_format PASSED
tests/test_middleware.py::test_correlation_id_uniqueness PASSED
tests/test_pii.py::test_scrub_email PASSED
tests/test_pii.py::test_scrub_phone_vn PASSED
... (12 more)
===== 15 passed in 0.38s =====
```
✅ 15/15 tests passed

---

## Tóm tắt kết quả nộp

| Kết quả | Giá trị | Cách lấy |
|---|---|---|
| validate_logs score | **100/100** | `python scripts/validate_logs.py` |
| Tests | **15/15 passed** | `python -m pytest tests/ -v` |
| Correlation IDs | **Unique req-XXXXXXXX** | Xem output load_test |
| PII Redaction | **0 leaks** | Grep logs cho REDACTED |
| Langfuse traces | **≥10 traces** | Mở cloud.langfuse.com |
| Dashboard | **6 panels** | Mở dashboard.html |
| Alert rules | **5 rules** | Mở config/alert_rules.yaml |
| Incident response | **460ms→2654ms→460ms** | inject_incident + load_test |
