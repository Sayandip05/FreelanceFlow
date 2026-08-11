# Architectural Decision Records (ADR)

A log of architectural and technical decisions made in FreelanceFlow explaining **why** choices were made, alternatives considered, and tradeoffs accepted. Ordered newest-first.

---

## 1. Google Gemini Embeddings for Qdrant Vector Memory
- **What**: Replaced `sentence-transformers` with Google Gemini `gemini-embedding-001` (3072-dimensional normalized vectors via REST API) for Qdrant contract vector memory.
- **Why**: Eliminates 500MB+ PyTorch/SentenceTransformers dependency bloat, reduces container cold-start and memory footprint to <150MB, and provides higher semantic accuracy.
- **Alternatives considered**: Local PyTorch embeddings (high memory and CPU load), `pgvector` in PostgreSQL (adds compute load to relational DB), OpenAI Embeddings (higher API cost).
- **Tradeoff accepted**: Outbound network dependency on Google Generative Language API; mitigated with a deterministic 3072-dim fallback vector generator if the API is unreachable.

---

## 2. Multi-Tier AI Agent Resiliency (Groq Primary + Gemini Fallback)
- **What**: 3-Node stateful LangGraph agent (`context_assembler` → `report_generator` → `pdf_builder`) with primary Groq LLaMA 3.3 70B and automated Google Gemini 2.0 Flash REST fallback.
- **Why**: Delivers ultra-low latency (<1.5s) inference via Groq LPUs while guaranteeing zero user downtime if Groq experiences rate limits or service outages.
- **Alternatives considered**: Single LLM provider (creates a single point of failure), asynchronous Celery queues for chat (breaks real-time interactive UX).
- **Tradeoff accepted**: Maintaining dual-provider prompt schema alignment; prompt outputs are strictly constrained to JSON schemas.

---

## 3. Database Indexing Strategy & N+1 Query Elimination
- **What**: Applied cardinality-first composite B-Tree indexes across all 8 apps (`users`, `projects`, `bidding`, `payments`, `worklogs`, `messaging`, `notifications`, `search`) and enforced zero-N+1 eager loading via `selectors.py`.
- **Why**: Multi-column composite indexes (e.g., `['status', '-created_at']`, `['contract', 'status']`) eliminate sequential table scans and in-memory sorting. Explicit `select_related`/`prefetch_related` on all multi-hop relation chains (`bid__project__client__client_profile`) prevents database roundtrips in DRF nested serializers.
- **Alternatives considered**: Single-column indexes on all filter fields (causes write amplification without solving multi-column filters), relying on Redis caching alone (stale cache risks).
- **Tradeoff accepted**: Minor write overhead on table inserts/updates in exchange for sub-millisecond read queries on critical paths.

---

## 4. Azure Blob Storage with Time-Limited SAS URLs for Media & PDFs
- **What**: Replaced AWS S3 with Azure Blob Storage (`azure-storage-blob` + `django-storages`) using 7-day read-only Shared Access Signatures (SAS) for PDFs, delivery proofs, and worklog screenshots.
- **Why**: Centralized cloud storage decoupled from ephemeral server disks; SAS tokens allow direct client downloads without exposing backend storage credentials or routing file payloads through Django.
- **Alternatives considered**: AWS S3 (migrated away per cloud vendor requirements), serving files via Django `FileResponse` (binds web workers during file downloads).
- **Tradeoff accepted**: SAS URLs expire after 7 days and must be refreshed via API endpoints for subsequent downloads.

---

## 5. Single-Process Daphne ASGI with InMemoryChannelLayer for WebSockets
- **What**: Configured Django Channels to use `InMemoryChannelLayer` exclusively, prohibiting `channels-redis` and running Daphne as the unified ASGI server.
- **Why**: Eliminates Redis Pub/Sub overhead and extra worker daemons for real-time messaging on single-node instances, strictly adhering to infrastructure budget constraints.
- **Alternatives considered**: `channels_redis` with Redis Pub/Sub (unnecessary complexity and Redis connection consumption for current deployment scale), client-side polling.
- **Tradeoff accepted**: Cannot broadcast WebSocket events across multiple distributed server nodes; must be revisited only if scaling to a multi-node cluster.

---

## 6. Upstash Redis Reserved Exclusively for Celery Task Queues
- **What**: Restricted Upstash Redis usage strictly to 3 pre-defined Celery queues (`freelanceflow_default`, `freelanceflow_high_priority`, `freelanceflow_low_priority`), banning Redis for caching, sessions, or channels.
- **Why**: Serverless Redis (Upstash) has strict concurrency and request quotas; dedicating it purely to Celery prevents connection exhaustion and unexpected billing spikes.
- **Alternatives considered**: Sharing Redis across sessions, cache, channels, and Celery (risks connection drops and eviction of task queues), RabbitMQ (heavier operational footprint).
- **Tradeoff accepted**: Sessions remain in PostgreSQL, and Django caching uses local memory.

---

## 7. Service-Selector Layering Architecture
- **What**: Enforced strict separation where all read queries reside in `selectors.py` and all business mutations/side-effects reside in `services.py`, keeping ViewSets and Models thin.
- **Why**: Centralizes business logic, prevents query duplication, makes business operations independently testable without HTTP mock layers, and guarantees consistent prefetching.
- **Alternatives considered**: Fat Django models (causes circular imports and tight coupling), putting querysets directly in ViewSets (duplicates logic across views and tasks).
- **Tradeoff accepted**: Additional boilerplate files (`selectors.py` and `services.py`) per Django app instead of standard generic DRF views.

---

## 8. Razorpay Milestone Escrow & Webhook Idempotency
- **What**: Milestone-based escrow payments with server-side HMAC-SHA256 signature verification and dedicated `PaymentEvent` idempotency tracking before releasing funds via RazorpayX.
- **Why**: Prevents double-credit and replay attacks from duplicate webhook events while ensuring client funds are safely locked until deliverable approval.
- **Alternatives considered**: Synchronous payment confirmation on the frontend (vulnerable to client tampering), holding full project funds in single lump sums without milestones.
- **Tradeoff accepted**: Asynchronous escrow confirmation dependent on external Razorpay webhook delivery.

---

## 9. Tamper-Evident Delivery Proofs & Escrow Release Protection
- **What**: Cryptographic report identifiers (`RPT-{draft.id}-{timestamp}`) and immutable `DeliveryProof` snapshots generated upon client milestone approval and Razorpay escrow release.
- **Why**: Guarantees non-repudiation and auditability during dispute resolution without relying on mutable worklog records.
- **Alternatives considered**: Dynamically rendering proof PDFs on-demand (subject to data modifications), storing raw HTML in DB.
- **Tradeoff accepted**: Permanent storage footprint for static PDF artifacts in Azure Blob Storage.

---

## 10. Dual-Blind Review System with Auto-Publish Timeout
- **What**: Both client and freelancer reviews remain hidden until both parties submit their review or a 14-day timeout expires.
- **Why**: Prevents retaliatory negative reviews and review extortion, ensuring objective ratings for both parties.
- **Alternatives considered**: Instant public review posting (leads to retaliatory 1-star ratings), admin-moderated reviews (creates operational bottleneck).
- **Tradeoff accepted**: Review visibility is delayed until the counterparty reviews or the 14-day window lapses.

---

## 11. Elasticsearch 8 Dual Inverted Index for Hybrid Search
- **What**: Dedicated Elasticsearch 8 indices (`projects` and `freelancers`) synchronized via Celery signal handlers alongside database query analytics (`SearchHistory`, `SearchSuggestion`).
- **Why**: Enables typo-tolerant fuzzy matching, multi-field boosting (title > skills > description), and sub-10ms response times on large marketplace catalogs without heavy SQL `ILIKE` queries.
- **Alternatives considered**: PostgreSQL Trigram / `pg_trgm` full-text search (degrades database performance at high concurrency), Algolia (high third-party vendor cost).
- **Tradeoff accepted**: Requires maintaining an external Elasticsearch service and handling eventual consistency on document updates.

---

## 12. TOTP Two-Factor Authentication with Static Backup Codes
- **What**: Time-based One-Time Password (TOTP) 2FA using `pyotp` with 10 pre-generated cryptographically secure backup codes stored in PostgreSQL.
- **Why**: Standardized, cost-free 2FA that does not depend on SMS gateway costs, carrier delivery failures, or third-party identity providers.
- **Alternatives considered**: SMS OTP via Twilio (incurs per-SMS charges and SIM-swapping risks), Email-based OTP (slower and vulnerable to email compromise).
- **Tradeoff accepted**: Users must install an authenticator app (Google Authenticator, Authy); account recovery requires backup codes or manual admin intervention.

---

## 13. Soft Account Deactivation with 30-Day Grace Period
- **What**: Users can soft-deactivate their accounts (`is_deactivated=True`, `deactivated_at`), hiding profiles while preserving active contracts and transaction audit trails for 30 days before full erasure.
- **Why**: Prevents accidental permanent data loss and preserves financial/tax history required for escrow dispute resolution and regulatory compliance.
- **Alternatives considered**: Immediate hard delete (`CASCADE`) upon user request (destroys contract and escrow payment history).
- **Tradeoff accepted**: Retaining deactivated user rows in the database; requires filtering `is_deactivated=False` across user directory queries.

---

## 14. Standardized Domain Exception Hierarchy (`core.exceptions`)
- **What**: Unified domain exception classes (`ValidationError`, `BusinessError`, `PermissionDeniedError`, `NotFoundError`) mapped via custom DRF exception handler (`custom_exception_handler`).
- **Why**: Ensures uniform, predictable JSON error envelopes across all 8 domain apps (`{"error": {"code": "...", "message": "...", "field": "..."}}`), simplifying frontend error handling.
- **Alternatives considered**: Relying on raw DRF `APIException` subclasses (inconsistent structure across standard vs custom errors), returning HTTP 200 with error codes in payload.
- **Tradeoff accepted**: Services must raise explicit domain exceptions rather than returning raw boolean or tuple error indicators.

---

## 15. Multi-Channel Notification Preference Matrix
- **What**: Centralized notification router supporting in-app, email, and WebPush (FCM) driven by a 21-event boolean matrix in `NotificationPreference`.
- **Why**: Empowers users to customize alert channels per event type while preventing platform notification spam and unneeded email delivery costs.
- **Alternatives considered**: Hardcoded notification rules per event, single global toggle (all on / all off).
- **Tradeoff accepted**: Additional lookup on `NotificationPreference` for every notification event before dispatching background delivery tasks.

---

## 16. Entity Normalization vs. Single-Table Inlining (1-to-1 Schema Consolidation)
- **What**: Consolidated redundant 1-to-1 extension models (`BidRetraction`, `ReviewResponse`, `WorklogApproval`, `MultiCurrencyPayment`, `ProjectShare`) directly into their root parent entities (`Bid`, `Review`, `WorkLog`, `Payment`, `Project`), while strictly preserving separate tables for models with distinct lifecycles, high-churn write isolation, or 1-to-many audit trails (`Escrow`, `PaymentEvent`, `WorkLog`, `ActivityLog`).
- **Why**: Eliminates unnecessary SQL `JOIN`s, reverse OneToOne prefetching overhead, and dual-state synchronization bugs across app boundaries, reducing schema table count by ~20% while keeping write-heavy audit logs isolated.
- **Alternatives considered**: Retaining fragmented extension models across multiple `models_*.py` files, completely denormalizing all sub-entities into monolithic JSONB blobs.
- **Tradeoff accepted**: Parent entity tables contain a few additional nullable metadata columns (e.g., `retraction_reason`, `response_text`) in exchange for single-query fetches and simpler serialization graphs.
