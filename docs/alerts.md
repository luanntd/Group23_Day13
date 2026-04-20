# Alert Rules and Runbooks

## 1. High latency P95
- Severity: P2
- Trigger: `latency_p95_ms > 5000 for 30m`
- Impact: tail latency breaches SLO
- First checks:
  1. Open top slow traces in the last 1h
  2. Compare RAG span vs LLM span
  3. Check if incident toggle `rag_slow` is enabled
- Mitigation:
  - truncate long queries
  - fallback retrieval source
  - lower prompt size

## 2. High error rate
- Severity: P1
- Trigger: `error_rate_pct > 5 for 5m`
- Impact: users receive failed responses
- First checks:
  1. Group logs by `error_type`
  2. Inspect failed traces
  3. Determine whether failures are LLM, tool, or schema related
- Mitigation:
  - rollback latest change
  - disable failing tool
  - retry with fallback model

## 3. Cost budget spike
- Severity: P2
- Trigger: `hourly_cost_usd > 2x_baseline for 15m`
- Impact: burn rate exceeds budget
- First checks:
  1. Split traces by feature and model
  2. Compare tokens_in/tokens_out
  3. Check if `cost_spike` incident was enabled
- Mitigation:
  - shorten prompts
  - route easy requests to cheaper model
  - apply prompt cache

## 4. Quality score drop
- Severity: P2
- Trigger: `quality_avg < 0.60 for 15m`
- Impact: response quality degradation, user trust erosion
- First checks:
  1. Check quality_avg trend in dashboard
  2. Filter traces with quality_score < 0.5
  3. Check if RAG retrieval is returning fallback docs only
  4. Compare recent model responses for hallucination patterns
- Mitigation:
  - verify RAG corpus is accessible and up-to-date
  - check if model endpoint changed or degraded
  - temporarily route to higher-quality model
  - add fallback quality gate before returning response

## 5. Token budget exceeded
- Severity: P3
- Trigger: `tokens_out_total > 50000 per hour`
- Impact: unexpected cost increase, possible prompt injection or runaway generation
- First checks:
  1. Check tokens_in vs tokens_out ratio in dashboard
  2. Identify requests with unusually high token counts in traces
  3. Check if `cost_spike` incident toggle is active
  4. Review recent feature changes that may have altered prompt templates
- Mitigation:
  - set max_tokens limit on LLM calls
  - add output length guardrail
  - implement per-user rate limiting
  - alert finops team for budget review
