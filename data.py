# Synthetic postmortems: (service, alert, root cause, fix, worked)
INCIDENTS = [
 ("checkout-api","p99 latency 4.2s, Redis ETIMEDOUT after deploy 2024.31","Redis connection pool exhausted; new release doubled worker count","Raised pool max 50->200 and capped workers at 8",True),
 ("payments-worker","Queue depth 48k, consumers restarting, OOMKilled","Batch size 5000 loaded whole payloads in memory","Batch size 5000->500 and memory limit 1Gi->2Gi",True),
 ("checkout-api","p99 latency 3.8s, Redis ETIMEDOUT","Suspected Redis node failure","Failed over Redis primary",False),
 ("auth-service","502s from gateway, JWKS fetch timeouts","Identity provider JWKS endpoint slow; no cache","Added 10 min JWKS cache with stale-while-revalidate",True),
 ("search-api","CPU 98%, latency spike every 15 min","Cron reindex job overlapping with peak traffic","Moved reindex to 03:00 UTC and added lock",True),
 ("orders-db","Postgres connections 500/500, 'too many clients'","Idle-in-transaction sessions from a leaked ORM session","Set idle_in_transaction_session_timeout=30s, fixed session leak",True),
 ("orders-db","Replica lag 90s, read errors","Long analytics query on replica","Killed query, routed analytics to a dedicated replica",True),
 ("notif-service","Email delivery rate dropped 60%, 429s from provider","Provider rate limit hit after marketing blast","Added token-bucket throttle and priority lanes",True),
 ("checkout-api","5xx spike right after deploy 2024.44, DB migration timeout","Migration added index without CONCURRENTLY, locked table","Rolled back, re-ran migration with CONCURRENTLY",True),
 ("gateway","TLS handshake failures for mobile clients","Expired intermediate cert in chain bundle","Reissued full chain bundle, added expiry alert at 30 days",True),
]
def as_text(i):
    s,a,c,f,w=i
    return f"Incident on {s}. Alert: {a}. Root cause: {c}. Fix attempted: {f}. Outcome: {'WORKED' if w else 'DID NOT WORK'}."
