# Oncall Memory: an incident-response agent that learns (Hindsight hackathon)

An on-call copilot that remembers every incident, its root cause, the fix tried, and whether it worked.

## How Hindsight is used
- **Retain**: each postmortem (`/api/seed`) and each live outcome (`/api/resolve`, worked / didn't work).
- **Recall**: every new alert queries the bank for similar past incidents; results are injected into the LLM prompt (`/api/triage`).
- **Reflect**: `/api/insights` asks Hindsight to synthesize recurring patterns and permanent fixes.
- **Before/after**: the "Use team memory" toggle runs the same alert with and without memory.

## Run
```
pip install -r requirements.txt
cp .env.example .env   # add Hindsight Cloud + Groq keys (promo: MEMHACK99)
uvicorn app:app --reload
```
Open http://localhost:8000, click **Load sample incidents**, then try the demo below.

## Demo script (60s)
1. Alert: `checkout-api p99 latency 4s, Redis ETIMEDOUT after deploy`, memory OFF: generic advice.
2. Same alert, memory ON: cites the pool-exhaustion incident and warns that a Redis failover did NOT work.
3. Log a new outcome, re-run a similar alert, and it now cites your latest fix.
4. Click **Reflect** for recurring patterns.

Groq function-call/rate-limit errors are handled with retry plus a fallback model (`qwen/qwen3-32b`).
