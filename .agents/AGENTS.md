# FreelanceFlow Project Rules & Infrastructure Constraints

## 1. Django Channels / WebSocket Configuration
- **STRICT RULE**: Always use `InMemoryChannelLayer`, nothing else:
  ```python
  CHANNEL_LAYERS = {
      "default": {
          "BACKEND": "channels.layers.InMemoryChannelLayer"
      }
  }
  ```
- Never add `channels_redis`, `RedisChannelLayer`, or any Redis-based channel layer anywhere. Ever.
- A single Daphne process handles all WebSocket connections as async coroutines.
- `InMemoryChannelLayer` routes messages between consumers directly inside that single process.

## 2. Celery Workers & Queues
- **STRICT RULE**: Never add new Celery workers or queues.
- Existing queues are final:
  - `freelanceflow_default`
  - `freelanceflow_high_priority`
  - `freelanceflow_low_priority`
- Never create a new Celery worker or queue for any reason.
- Never route chat, messaging, or WebSocket tasks to Celery.
- WebSocket messages are handled by Daphne async consumers directly — zero worker involvement, zero queue involvement.

## 3. Redis Usage
- **STRICT RULE**: Upstash Redis is used **ONLY** for Celery task queues.
- No new Redis usage. No new Redis connections.
- No Redis for sessions, cache, channels, or messaging.

## 4. Daphne Process Model
- Daphne handles all WebSocket connections as async coroutines in one process.
- No extra infrastructure, daemons, or services needed.
- If you feel the urge to add a worker, a queue, or Redis for anything chat/WebSocket related — stop. The answer is always: Daphne handles it, InMemory routes it.
