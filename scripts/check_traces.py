import httpx
import json

pk = "pk-lf-75aab663-8d78-46e0-ad22-d4d20364809b"
sk = "sk-lf-7f650790-3294-41e6-b383-1622ac548d53"
host = "https://cloud.langfuse.com"

print("=== 1. PROJECTS ===")
try:
    r = httpx.get(f"{host}/api/public/projects", auth=(pk, sk), timeout=10)
    print(f"Status: {r.status_code}")
    print(r.text[:500])
except Exception as e:
    print(f"Projects endpoint error: {e}")

print("\n=== 2. ALL TRACES ===")
r2 = httpx.get(f"{host}/api/public/traces?limit=50", auth=(pk, sk), timeout=10)
data = r2.json()
traces = data.get("data", [])
print(f"Total traces returned: {len(traces)}")
for i, t in enumerate(traces[:10]):
    tid = t.get("id", "?")[:16]
    name = t.get("name", "?")
    ts = t.get("timestamp", "?")
    pid = t.get("projectId", "?")
    print(f"  [{i}] {name} | project={pid} | time={ts}")

if traces:
    pid = traces[0].get("projectId", "unknown")
    print(f"\nDirect URL: https://cloud.langfuse.com/project/{pid}/traces")

print("\n=== 3. TRACE DETAIL (first trace) ===")
if traces:
    first_id = traces[0]["id"]
    r3 = httpx.get(f"{host}/api/public/traces/{first_id}", auth=(pk, sk), timeout=10)
    detail = r3.json()
    print(f"Name: {detail.get('name')}")
    print(f"User: {detail.get('userId')}")
    print(f"Session: {detail.get('sessionId')}")
    print(f"Tags: {detail.get('tags')}")
    print(f"Input: {json.dumps(detail.get('input', {}))[:100]}")
    print(f"Output: {json.dumps(detail.get('output', {}))[:100]}")
    print(f"Observations: {len(detail.get('observations', []))}")

print("\n=== 4. HEALTH CHECK ===")
r4 = httpx.get(f"{host}/api/public/health", auth=(pk, sk), timeout=10)
print(f"Health: {r4.status_code} {r4.text[:100]}")
