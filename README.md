# SMS Gateway - Technical Design Document

## Overview
High-throughput SMS gateway supporting ~100M messages/day with regular and express delivery (SLA < 500ms for express).

---

## Architecture Decisions & Trade-offs

### 1. **Service Boundaries**
- **Decision**: Gateway does not handle authentication or billing.
- **Rationale**: API key validation only (no user management). Balance is pre-loaded, gateway just validates and deducts. Simplifies design and isolates concerns.

### 2. **Database Design**

#### Table Partitioning (Range by `created_at`)
- **Decision**: Monthly partitions on `sms` table.
- **Rationale**:
  - ~100M messages/day = ~3B/month ’ single table becomes unmaintainable
  - Partition pruning: queries filtered by date only scan relevant partitions
  - Easy archival: drop old partitions instead of expensive DELETEs
  - **Trade-off**: Adds operational complexity (automated partition creation needed)

#### B-Tree vs Hash Index for `api_key`
- **Decision**: B-Tree index (default).
- **Rationale**: PostgreSQL UNIQUE constraint requires B-Tree. Hash indexes don't support uniqueness checks and have limited use cases in Postgres.

### 3. **Concurrency & Race Conditions**

#### Balance Deduction (ACID Guarantee)
```python
UPDATE accounts
SET balance = balance - 1
WHERE id = $1 AND balance >= 1
```
- **Decision**: Atomic SQL operation with conditional check.
- **Rationale**: Database handles concurrency via row-level locking. Prevents race conditions without application-level locks.

#### API Key Caching
- **Decision**: Cache full account object in Redis (12-hour TTL).
- **Rationale**: Avoid DB query on every SMS request. Stale balance acceptable (eventual consistency) since actual deduction happens in DB transaction.
- **Trade-off**: 12-hour stale data vs 95%+ cache hit rate.

### 4. **Message Queue Architecture**

#### Celery vs Custom Consumer
- **Decision**: Use Celery workers instead of custom RabbitMQ consumer.
- **Rationale**:
  - Built-in retry, backoff, monitoring
  - Time constraint: custom consumer adds 2-3 days development
  - **Trade-off**: Less control over message handling, but 80% faster implementation

#### Prefetch Count = 1000
- **Decision**: Workers pull 1000 tasks at once from RabbitMQ.
- **Rationale**: Reduces network round-trips. Worker processes tasks sequentially but has them queued locally.
- **Trade-off**: If worker crashes, up to 1000 tasks are requeued (acceptable with `task_acks_late`).

### 5. **Batch Processing**

#### Redis-Based Batching
```
Worker ’ Send to Operator ’ Push result to Redis list
Beat Task (every 2s) ’ Pull 10K results ’ Batch UPDATE DB
```
- **Decision**: Accumulate status updates in Redis, batch write every 2 seconds.
- **Rationale**:
  - 1000 individual UPDATEs ’ 1 batch UPDATE (100x fewer DB round-trips)
  - Single transaction for atomicity
  - **Trade-off**: 2-second latency for status updates (acceptable for analytics)

#### Redis AOF Persistence
- **Decision**: `appendonly yes` with `appendfsync everysec`.
- **Rationale**: Prevents data loss if Redis crashes mid-batch. Max 1-second loss acceptable.

#### Graceful Degradation
```python
try:
    await redis.lpush("sms_results", ...)
except:
    await repo.update_status(...)  # Direct DB fallback
```
- **Decision**: If Redis unavailable, fall back to individual DB updates.
- **Rationale**: Availability > Performance during failures. System remains operational.

### 6. **Failure Handling**

#### Dead Letter Queue (DLQ)
- **Decision**: Tasks failing after 3 retries go to DLQ for investigation.
- **Rationale**: Prevents infinite loops while preserving failed tasks for debugging.
- **Implementation**: `on_failure()` hook sends task metadata to DLQ queue.

#### Retry Strategy
- **Exponential backoff**: 2s, 4s, 8s delays (max 3 retries)
- **Rationale**: Transient failures (network glitch) recover quickly. Permanent failures (bad data) fail fast.

#### Automatic Requeue
- **`task_acks_late = True`**: Tasks acknowledged only after completion.
- **Rationale**: Worker crash ’ RabbitMQ auto-requeues unprocessed tasks. Zero message loss during deployments.

### 7. **Operator Failover**
- **Priority-based routing**: Try operator_1 ’ operator_2 ’ operator_3
- **Circuit breaker**: 3 attempts per operator with exponential backoff
- **Trade-off**: Increases delivery latency (up to 9 retries total) but maximizes success rate

---

## Performance Optimizations

| Optimization | Impact | Trade-off |
|-------------|---------|-----------|
| Redis API key cache | 95% cache hit ’ ~10x faster auth | 12-hour stale data |
| Batch DB updates | 100x fewer queries | 2-second status delay |
| Prefetch count=1000 | Reduced network overhead | Requeue overhead on crash |
| Table partitioning | Query time O(1/12) for date filters | Operational complexity |

---

## Scalability Considerations

- **Horizontal scaling**: Stateless workers ’ add more containers
- **Queue separation**: Express (SLA < 500ms) and regular queues
- **Database**: Partitioning supports 100M+/day. Further scaling via sharding by `account_id`
- **Redis**: AOF persistence with optional Sentinel for HA

---

## System Guarantees

 **At-least-once delivery**: `task_acks_late` ensures no message loss
 **Idempotency**: SMS `id` is UUID ’ safe to retry
 **Consistency**: Balance deduction is atomic (ACID)
 **Availability**: Graceful degradation when Redis/operators fail

---

## Technology Stack

- **FastAPI**: Async API framework
- **PostgreSQL 16**: Partitioned tables, ACID transactions
- **Redis 7**: Caching + batch accumulation (AOF enabled)
- **RabbitMQ 3**: Message broker (express/regular queues)
- **Celery**: Task queue with retry/DLQ support
- **Docker Compose**: Containerized deployment
