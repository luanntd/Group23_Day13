import httpx
import json
import uuid
import datetime

pk = "pk-lf-75f20aa6-c4cf-4054-935c-47f189f62d81"
sk = "sk-lf-336dfea4-c833-40e5-bae1-7aeeb51106ef"
host = "http://localhost:3000"

# Auth check
r = httpx.get(f"{host}/api/public/health", auth=(pk, sk), timeout=10)
print(f"Health: {r.status_code} {r.text[:50]}")

# Send 20 traces
for i in range(20):
    tid = str(uuid.uuid4())
    payload = {
        "batch": [{
            "id": str(uuid.uuid4()),
            "type": "trace-create",
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat(),
            "body": {
                "id": tid,
                "name": f"lab13-agent-run-{i}",
                "userId": f"user-hash-{i:02d}",
                "sessionId": f"s{i:02d}",
                "tags": ["lab", "qa", "claude-sonnet-4-5"],
                "metadata": {"feature": "qa", "doc_count": 1, "model": "claude-sonnet-4-5"},
                "input": {"message": f"test query {i}"},
                "output": {"answer": f"AI response for query {i}"},
            }
        }]
    }
    r = httpx.post(f"{host}/api/public/ingestion", json=payload, auth=(pk, sk), timeout=10)
    status = "OK" if r.status_code in (200, 207) else "FAIL"
    print(f"Trace {i:2d}: {r.status_code} {status}")

# Verify
r2 = httpx.get(f"{host}/api/public/traces?limit=5", auth=(pk, sk), timeout=10)
data = r2.json()
traces = data.get("data", [])
print(f"\nVerification: {len(traces)} traces visible via API")
print(f"Open browser: http://localhost:3000")
