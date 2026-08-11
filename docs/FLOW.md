# Execution Flow & Call Graph (FLOW.md)

Detailed, verified execution call paths across all entry points (HTTP REST routes, WebSocket connections, Celery tasks, and signals) in the FreelanceFlow backend.

---

# 1. Authentication & Users Module (`apps/users`)

## POST `/api/users/register/`
- **Trigger**: HTTP POST request with user registration payload (`email`, `password`, `role`, `first_name`, `last_name`).
- **Path**: `apps/users/urls/urls.py:register` → `apps/users/views/views.py:RegisterView.post` → `apps/users/serializers/serializers.py:UserRegistrationSerializer.is_valid()` → `apps/users/services/services.py:create_user` → `django.contrib.auth.models.UserManager:create_user` → `apps/users/signals.py:create_user_profile` → `apps/users/tasks.py:send_welcome_email_task.delay`
- **Crosses**: Router → View → Serializer → Service → Model (DB write `users`) → Signal → Service (`freelancer_profiles` / `client_profiles`) → Celery Queue (`freelanceflow_default`).
- **Branches**:
  - Email already exists or validation fails → Raises `core.exceptions.ValidationError` (HTTP 400).
  - Invalid role enum → Raises `core.exceptions.ValidationError` (HTTP 400).
  - Success → Creates user & profile in `transaction.atomic()`, dispatches welcome email task, returns tokens + serialized user (HTTP 201).
- **Side effects**: DB insert into `users`, DB insert into `freelancer_profiles` or `client_profiles`, Celery background task queued for welcome email.

---

## POST `/api/users/login/`
- **Trigger**: HTTP POST request with `email` and `password`.
- **Path**: `apps/users/urls/urls.py:login` → `apps/users/views/views.py:LoginView.post` → `apps/users/services/services.py:authenticate_user` → `django.contrib.auth:authenticate` → `apps/users/services/services_activity.py:log_activity` → `apps/users/tokens.py:generate_tokens_for_user`
- **Crosses**: Router → View → Service → Django Auth Backend → Database read `users` → Service (DB insert `activity_logs`) → JWT Token Generator.
- **Branches**:
  - Invalid credentials / account deactivated → Raises `core.exceptions.ValidationError` (HTTP 401).
  - 2FA enabled (`TwoFactorAuth.is_enabled=True`) → Returns `{ "2fa_required": true, "temp_token": "..." }` (HTTP 200).
  - Success (2FA disabled) → Returns access + refresh tokens, user profile (HTTP 200).
- **Side effects**: DB insert into `activity_logs`, updates `user.last_login`.

---

## GET `/api/users/me/`
- **Trigger**: HTTP GET request with Bearer JWT token.
- **Path**: `apps/users/urls/urls.py:profile` → `apps/users/views/views.py:ProfileView.get` → `apps/users/selectors.py:get_user_profile` → `apps/users/serializers/serializers.py:UserDetailSerializer`
- **Crosses**: Router → Auth Middleware → View → Selector (`select_related('freelancer_profile', 'client_profile')`) → Serializer.
- **Branches**:
  - Unauthenticated → HTTP 401 Unauthorized.
  - User not found → Raises `core.exceptions.NotFoundError` (HTTP 404).
  - Success → Returns full serialized user + nested profile (HTTP 200).
- **Side effects**: None (Read-only).

---

## PATCH `/api/users/me/`
- **Trigger**: HTTP PATCH request to update profile details.
- **Path**: `apps/users/urls/urls.py:profile` → `apps/users/views/views.py:ProfileView.patch` → `apps/users/services/services.py:update_profile` → `apps/users/services/services_activity.py:log_activity`
- **Crosses**: Router → View → Service → DB write (`users`, `freelancer_profiles` or `client_profiles`) → DB write (`activity_logs`).
- **Branches**:
  - Validation error on hourly rate or bio length → Raises `core.exceptions.ValidationError` (HTTP 400).
  - Success → Updates profile fields inside `transaction.atomic()`, returns updated user (HTTP 200).
- **Side effects**: DB update on profile table, DB insert into `activity_logs`.

---

## POST `/api/users/avatar/`
- **Trigger**: HTTP POST request with multipart image upload.
- **Path**: `apps/users/urls/urls.py:update-avatar` → `apps/users/views/views.py:UpdateAvatarView.post` → `apps/users/services/services.py:update_avatar` → `apps/worklogs/services/pdf_service.py:upload_to_azure_blob`
- **Crosses**: Router → View → Service → Azure Blob Storage API → DB update on profile `avatar`.
- **Branches**:
  - Unsupported file MIME type or file size > 5MB → Raises `core.exceptions.ValidationError` (HTTP 400).
  - Success → Uploads blob to Azure container `media/avatars/`, updates profile `avatar` URL, returns SAS URL (HTTP 200).
- **Side effects**: External HTTPS upload to Azure Blob Storage, DB update on profile.

---

## POST `/api/users/status/heartbeat/`
- **Trigger**: HTTP POST heartbeat ping from active browser client.
- **Path**: `apps/users/urls/urls_extended.py:status-heartbeat` → `apps/users/views/views_extended.py:OnlineStatusViewSet.heartbeat` → `apps/users/services/services_status.py:update_online_status`
- **Crosses**: Router → View → Service → DB upsert `user_online_status`.
- **Branches**:
  - Success → Upserts `UserOnlineStatus(is_online=True, last_seen=now())` (HTTP 200).
- **Side effects**: DB update/insert into `user_online_status`.

---

# 2. Projects Module (`apps/projects`)

## POST `/api/projects/`
- **Trigger**: HTTP POST request from Client creating a new project.
- **Path**: `apps/projects/urls/urls.py:project-list` → `apps/projects/views/views.py:ProjectViewSet.create` → `apps/projects/serializers/serializers.py:ProjectCreateSerializer.is_valid()` → `apps/projects/services/services.py:create_project` → `apps/projects/signals.py:sync_project_to_elasticsearch` → `apps/search/tasks.py:index_project_task.delay`
- **Crosses**: Router → View → Serializer → Service → DB write `projects` → DB write `project_skills` → Signal → Celery Queue (`freelanceflow_low_priority`).
- **Branches**:
  - User role != CLIENT → Raises `core.exceptions.PermissionDeniedError` (HTTP 403).
  - Budget < minimum threshold → Raises `core.exceptions.ValidationError` (HTTP 400).
  - Success → Saves project as `OPEN` or `DRAFT`, bulk creates `ProjectSkill` records, dispatches Elasticsearch indexing task (HTTP 201).
- **Side effects**: DB inserts into `projects` and `project_skills`, Celery async task dispatched to index project in Elasticsearch.

---

## GET `/api/projects/`
- **Trigger**: HTTP GET request to browse open projects.
- **Path**: `apps/projects/urls/urls.py:project-list` → `apps/projects/views/views.py:ProjectViewSet.list` → `apps/projects/selectors.py:get_open_projects` → `apps/projects/serializers/serializers.py:ProjectListSerializer`
- **Crosses**: Router → View → Selector (`select_related('client__client_profile')`, `prefetch_related('skills')`) → Serializer.
- **Branches**:
  - Filter parameters provided (`budget_min`, `budget_max`, `skills`, `search`) → Applies QuerySet filter clauses and returns paginated list (HTTP 200).
- **Side effects**: None (Read-only).

---

## POST `/api/projects/{id}/publish/`
- **Trigger**: HTTP POST request by client to publish a draft project.
- **Path**: `apps/projects/urls/urls.py:project-publish` → `apps/projects/views/views.py:ProjectViewSet.publish` → `apps/projects/services/services.py:publish_project` → `apps/search/tasks.py:index_project_task.delay`
- **Crosses**: Router → View → Service → DB update `projects` (`status='OPEN'`) → Celery Queue.
- **Branches**:
  - User is not project owner → Raises `PermissionDeniedError` (HTTP 403).
  - Project not in `DRAFT` status → Raises `ValidationError` (HTTP 400).
  - Success → Updates status to `OPEN`, publishes to marketplace, queues ES re-indexing (HTTP 200).
- **Side effects**: DB update on `projects`, Celery task dispatched.

---

## POST `/api/projects/bookmarks/`
- **Trigger**: HTTP POST request by freelancer to bookmark a project.
- **Path**: `apps/projects/urls/urls_extended.py:bookmark-list` → `apps/projects/views/views_extended.py:ProjectBookmarkViewSet.create` → `apps/projects/services/services_bookmark.py:add_project_bookmark`
- **Crosses**: Router → View → Service → DB insert `project_bookmarks`.
- **Branches**:
  - Already bookmarked → Idempotent return existing bookmark (HTTP 200).
  - Success → Creates `ProjectBookmark` record (HTTP 201).
- **Side effects**: DB insert into `project_bookmarks`.

---

# 3. Bidding & Contracts Module (`apps/bidding`)

## POST `/api/bidding/bids/` (Alias: `POST /api/bids/`)
- **Trigger**: HTTP POST request from freelancer submitting a proposal.
- **Path**: `apps/bidding/urls/urls.py:bid-list` → `apps/bidding/views/views.py:BidViewSet.create` → `apps/bidding/services/services.py:submit_bid` → `apps/notifications/services/services.py:create_notification` → `apps/notifications/tasks.py:send_email_notification_task.delay`
- **Crosses**: Router → View → Service → DB write `bids` → Service (`apps/notifications`) → Celery Queue (`freelanceflow_default`).
- **Branches**:
  - User role != FREELANCER → Raises `PermissionDeniedError` (HTTP 403).
  - Project status != OPEN → Raises `ValidationError` (HTTP 400).
  - Freelancer already submitted active bid → Raises `ValidationError` (HTTP 400).
  - Success → Creates `Bid(status='PENDING')`, creates notification for project client, queues email (HTTP 201).
- **Side effects**: DB insert into `bids`, DB insert into `notifications`, Celery email task queued.

---

## POST `/api/bidding/bids/{id}/accept/`
- **Trigger**: HTTP POST request from client accepting a freelancer proposal.
- **Path**: `apps/bidding/urls/urls.py:bid-accept` → `apps/bidding/views/views.py:BidViewSet.accept` → `apps/bidding/services/services.py:accept_bid` → `apps/worklogs/signals.py:trigger_qdrant_initialization_on_contract_active` → `apps/worklogs/tasks.py:initialize_qdrant_collection_task.delay`
- **Crosses**: Router → View → Service → DB write `bids` (status='ACCEPTED') → DB write `contracts` (status='ACTIVE') → DB update `projects` (status='IN_PROGRESS') → Signal → Celery Queue (`freelanceflow_default`).
- **Branches**:
  - Requester != project client → Raises `PermissionDeniedError` (HTTP 403).
  - Bid status != PENDING → Raises `ValidationError` (HTTP 400).
  - Success → Executes inside `transaction.atomic()`: marks bid accepted, rejects competing bids, creates `Contract`, updates project to `IN_PROGRESS`, fires signal to initialize Qdrant vector memory in background (HTTP 200).
- **Side effects**: DB updates on `bids` and `projects`, DB insert into `contracts`, Celery task dispatched to populate Qdrant vector collection.

---

## POST `/api/bidding/bids/{id}/retract/`
- **Trigger**: HTTP POST request by freelancer to withdraw their proposal.
- **Path**: `apps/bidding/urls/urls_extended.py:retraction-list` → `apps/bidding/views/views_extended.py:BidRetractionViewSet.create` → `apps/bidding/services/services_retraction.py:retract_bid`
- **Crosses**: Router → View → Service → DB update `bids` (`status='WITHDRAWN'`).
- **Branches**:
  - Bid already accepted or contracted → Raises `ValidationError` (HTTP 400).
  - Exceeded retraction limit (max 3/month) → Raises `ValidationError` (HTTP 400).
  - Success → Marks bid withdrawn and logs reason (HTTP 200).
- **Side effects**: DB update on `bids`.

---

## POST `/api/bidding/contracts/{id}/complete/`
- **Trigger**: HTTP POST request from client to mark contract finished.
- **Path**: `apps/bidding/urls/urls.py:contract-complete` → `apps/bidding/views/views.py:ContractViewSet.complete` → `apps/bidding/services/services.py:complete_contract` → `apps/worklogs/services/pdf_service.py:generate_delivery_proof_pdf`
- **Crosses**: Router → View → Service → DB update `contracts` (`status='COMPLETED'`) → DB insert `delivery_proofs` → Azure Blob Upload.
- **Branches**:
  - Pending unapproved deliverables exist → Raises `ValidationError` (HTTP 400).
  - Success → Transitions contract and project to `COMPLETED`, compiles immutable `DeliveryProof` PDF snapshot, uploads to Azure Blob Storage, returns proof URL (HTTP 200).
- **Side effects**: DB update on `contracts` and `projects`, DB insert into `delivery_proofs`, Azure Blob Storage upload.

---

## POST `/api/bidding/reviews/`
- **Trigger**: HTTP POST request submitting feedback after contract completion.
- **Path**: `apps/bidding/urls/urls.py:review-list` → `apps/bidding/views/views.py:ReviewViewSet.create` → `apps/bidding/services/services_review.py:create_review`
- **Crosses**: Router → View → Service → DB write `reviews` → DB update on profile `average_rating`.
- **Branches**:
  - Contract status != COMPLETED → Raises `ValidationError` (HTTP 400).
  - Dual-Blind Check: Counterparty has not reviewed yet → Stored with `is_public=False` until counterparty submits or 14 days lapse (HTTP 201).
  - Both parties reviewed → Sets `is_public=True` for both reviews, recalculates average ratings (HTTP 201).
- **Side effects**: DB insert into `reviews`, DB update on `freelancer_profiles` / `client_profiles`.

---

# 4. Payments & Escrow Module (`apps/payments`)

## POST `/api/payments/`
- **Trigger**: HTTP POST request from client creating an escrow order for contract/milestone.
- **Path**: `apps/payments/urls/urls.py:payment-list` → `apps/payments/views/views.py:PaymentViewSet.create` → `apps/payments/services/services.py:create_milestone_escrow` → `razorpay.Client:order.create`
- **Crosses**: Router → View → Service → External Razorpay API → DB write `payments` (`status='PENDING'`).
- **Branches**:
  - Requester != contract client → Raises `PermissionDeniedError` (HTTP 403).
  - Razorpay API communication error → Raises `ValidationError` (HTTP 502/400).
  - Success → Creates Razorpay order (in paise), creates local `Payment` record, returns `order_id` for checkout (HTTP 201).
- **Side effects**: External API call to Razorpay, DB insert into `payments`.

---

## POST `/api/payments/verify/`
- **Trigger**: HTTP POST request from frontend checkout callback with Razorpay payment signature.
- **Path**: `apps/payments/urls/urls.py:verify-payment` → `apps/payments/views/views.py:verify_payment` → `apps/payments/services/services.py:verify_razorpay_signature`
- **Crosses**: Router → View → Service (HMAC-SHA256 crypto validation) → DB write `payments` (`status='CAPTURED'`) → DB write `escrow` (`status='HELD'`).
- **Branches**:
  - Signature mismatch → Raises `ValidationError("Invalid signature")` (HTTP 400).
  - Success → Marks `Payment` as `CAPTURED`, creates `Escrow` record holding funds securely in escrow (HTTP 200).
- **Side effects**: DB updates on `payments` and inserts into `escrow`.

---

## POST `/api/payments/webhook/`
- **Trigger**: Inbound HTTP POST webhook from Razorpay servers.
- **Path**: `apps/payments/urls/urls.py:razorpay-webhook` → `apps/payments/views/views.py:razorpay_webhook` → `apps/payments/tasks.py:process_razorpay_webhook_task.delay`
- **Crosses**: Router → Webhook View (HMAC verification) → Celery Queue (`freelanceflow_high_priority`) → `apps/payments/services/services.py:handle_payment_captured`.
- **Branches**:
  - Webhook secret verification fails → Returns HTTP 400.
  - Event already processed (idempotency check via `PaymentEvent`) → Returns HTTP 200 (duplicate ignored).
  - Success → Queues async task to safely update escrow and contract state (HTTP 200).
- **Side effects**: DB insert into `payment_events`, DB update on `payments`/`escrow`.

---

## POST `/api/payments/{id}/release/`
- **Trigger**: HTTP POST request from client approving milestone work and releasing funds.
- **Path**: `apps/payments/urls/urls.py:payment-release` → `apps/payments/views/views.py:PaymentViewSet.release_escrow` → `apps/payments/services/services.py:release_milestone_escrow` → `apps/payments/tasks.py:process_payout_task.delay`
- **Crosses**: Router → View → Service → DB write `escrow` (`status='RELEASED'`) → DB write `platform_earnings` → Celery Queue.
- **Branches**:
  - Milestone deliverable not approved → Raises `ValidationError` (HTTP 400).
  - Success → Deducts platform cut (10%), credits freelancer earnings, queues RazorpayX payout task (HTTP 200).
- **Side effects**: DB updates on `escrow` and `freelancer_profiles`, DB insert into `platform_earnings`, Celery payout task dispatched.

---

# 5. AI Worklogs & Reports Module (`apps/worklogs`)

## POST `/api/worklogs/ai/chat/`
- **Trigger**: HTTP POST request from freelancer chatting with the AI assistant.
- **Path**: `apps/worklogs/urls/urls.py:ai-chat` → `apps/worklogs/views/views_ai.py:AIChatView.post` → `apps/worklogs/services/ai_service.py:run_ai_worklog_agent(action='chat')`
  1. `apps/worklogs/services/ai_service.py:context_assembler` → `apps/worklogs/services/qdrant_service.py:query_context` (Google Gemini `gemini-embedding-001` 3072-dim embeddings + Qdrant Cloud search).
  2. `apps/worklogs/services/ai_service.py:report_generator` → Groq LLaMA 3.3 70B API (or fallback `call_gemini_fallback_sync` Google Gemini 2.0 Flash) → DB persist `AIConversation` + `AIReportDraft(status='DRAFT')`.
- **Crosses**: Router → View → LangGraph Agent → PostgreSQL read → Qdrant Vector Cloud → Groq / Google Gemini LLM API → DB write (`ai_conversations`, `ai_report_drafts`).
- **Branches**:
  - User is not contract freelancer → Raises `PermissionDeniedError` (HTTP 403).
  - Groq offline/rate limited → Automatically invokes Google Gemini fallback via REST API.
  - LLM offline → Employs deterministic structured 3-section rule synthesizer.
  - Success → Returns assistant reply and structured 3-section draft data (HTTP 200).
- **Side effects**: DB insert/update in `ai_conversations`, DB insert in `ai_report_drafts`.

---

## POST `/api/worklogs/ai/approve/`
- **Trigger**: HTTP POST request from freelancer clicking "Approve Draft & Generate Official PDF".
- **Path**: `apps/worklogs/urls/urls.py:ai-approve` → `apps/worklogs/views/views_ai.py:AIApproveDraftView.post` → `apps/worklogs/services/ai_service.py:run_ai_worklog_agent(action='approve')`
  1. `apps/worklogs/services/ai_service.py:pdf_builder` → `weasyprint.HTML().write_pdf()` (Compiles branded HTML with tamper-evident ID `RPT-{id}-{timestamp}`).
  2. `apps/worklogs/services/pdf_service.py:upload_to_azure_blob` (Uploads to Azure Blob Storage container `media/reports/`).
  3. DB update `AIReportDraft(status='APPROVED', pdf_url=sas_url)` and mirror to `WeeklyReport`.
- **Crosses**: Router → View → LangGraph Agent (pdf_builder) → WeasyPrint C-Engine → Azure Blob Storage HTTPS API → DB write (`ai_report_drafts`, `weekly_reports`).
- **Branches**:
  - Draft not found or not in DRAFT status → Raises `ValidationError` (HTTP 400).
  - Success → Compiles PDF, uploads to Azure Blob Storage, marks approved, returns 7-day SAS URL (HTTP 200).
- **Side effects**: Azure Blob Storage upload, DB update on `ai_report_drafts`, DB insert/update on `weekly_reports`.

---

## GET `/api/worklogs/ai/context/?contract={id}`
- **Trigger**: HTTP GET request when opening the freelancer split-screen AI workspace.
- **Path**: `apps/worklogs/urls/urls.py:ai-context` → `apps/worklogs/views/views_ai.py:AIContextView.get` → `apps/worklogs/selectors_ai.py:get_contract_context_bundle`
- **Crosses**: Router → View → Selector (`select_related`, `prefetch_related` deliverables, previous reports, Qdrant collection status) → Response.
- **Branches**:
  - Requester != freelancer → Raises `PermissionDeniedError` (HTTP 403).
  - Success → Returns contract overview, deliverables checklist, active draft, stats, and Qdrant status (HTTP 200).
- **Side effects**: None (Read-only).

---

## POST `/api/worklogs/logs/`
- **Trigger**: HTTP POST request from freelancer logging daily work hours.
- **Path**: `apps/worklogs/urls/urls.py:worklog-list` → `apps/worklogs/views/views.py:WorkLogViewSet.create` → `apps/worklogs/services/services.py:create_worklog` → `apps/worklogs/tasks.py:notify_client_log_submitted.delay`
- **Crosses**: Router → View → Service → DB write `work_logs` → Celery Queue (`freelanceflow_default`).
- **Branches**:
  - Hours worked > 24 or <= 0 → Raises `ValidationError` (HTTP 400).
  - Log for same (contract, date) exists → Raises `ValidationError` (HTTP 400).
  - Success → Creates `WorkLog(status='PENDING_APPROVAL')`, notifies client (HTTP 201).
- **Side effects**: DB insert into `work_logs`, Celery notification task dispatched.

---

## POST `/api/worklogs/deliverables/{id}/approve/`
- **Trigger**: HTTP POST request from client approving a completed deliverable item.
- **Path**: `apps/worklogs/urls/urls.py:deliverable-approve` → `apps/worklogs/views/views.py:DeliverableViewSet.approve` → `apps/worklogs/services/services.py:approve_deliverable` → `apps/worklogs/services/qdrant_service.py:add_feedback`
- **Crosses**: Router → View → Service → DB update `deliverables` (`status='APPROVED'`) → Qdrant Vector Cloud.
- **Branches**:
  - Requester != client → Raises `PermissionDeniedError` (HTTP 403).
  - Success → Marks deliverable `APPROVED`, creates corresponding approved `WorkLog` entry, indexes client feedback into Qdrant (HTTP 200).
- **Side effects**: DB updates on `deliverables` and `work_logs`, Qdrant vector point upserted.

---

# 6. Real-time Messaging Module (`apps/messaging`)

## WebSocket `ws/chat/{contract_id}/`
- **Trigger**: WebSocket client handshake connecting to per-contract chat room.
- **Path**: `config/asgi.py:ProtocolTypeRouter` → `channels.auth:AuthMiddlewareStack` → `apps/messaging/routing.py:re_path` → `apps/messaging/consumers.py:ChatConsumer.connect`
  - On Connect: Validates user is contract participant → `channel_layer.group_add(f"chat_{contract_id}")` (InMemoryChannelLayer) → `accept()`.
  - On Message: `ChatConsumer.receive_json` → `apps/messaging/services/services.py:save_chat_message` → `channel_layer.group_send("chat_message")` → `ChatConsumer.chat_message`.
- **Crosses**: ASGI Server (Daphne) → Channels Middleware → Async Consumer → DB write `messaging_message` → `InMemoryChannelLayer` (Internal process memory) → WebSocket clients.
- **Branches**:
  - User unauthenticated or not in contract → Closes WebSocket connection (`close(code=4003)`).
  - Recipient offline → Dispatches async task to send email/push notification.
- **Side effects**: DB insert into `messaging_message`, in-memory broadcast to connected clients.

---

## GET `/api/messaging/conversations/`
- **Trigger**: HTTP GET request listing all conversations for authenticated user.
- **Path**: `apps/messaging/urls/urls.py:conversation-list` → `apps/messaging/views/views.py:ConversationViewSet.list` → `apps/messaging/selectors.py:get_user_conversations`
- **Crosses**: Router → View → Selector (`select_related('contract__bid__project')`) → Serializer.
- **Branches**:
  - Success → Returns conversations ordered by latest message timestamp (HTTP 200).
- **Side effects**: None (Read-only).

---

# 7. Notifications Module (`apps/notifications`)

## GET `/api/notifications/notifications/`
- **Trigger**: HTTP GET request to fetch user notifications.
- **Path**: `apps/notifications/urls/urls.py:notification-list` → `apps/notifications/views/views.py:NotificationViewSet.list` → `apps/notifications/selectors.py:get_user_notifications`
- **Crosses**: Router → View → Selector (`Notification.objects.filter(recipient=user).order_by('-created_at')`) → Serializer.
- **Branches**:
  - Query param `unread=true` → Filters `is_read=False`.
  - Success → Returns paginated notification items (HTTP 200).
- **Side effects**: None (Read-only).

---

## POST `/api/notifications/notifications/{id}/mark-read/`
- **Trigger**: HTTP POST request when user clicks a notification.
- **Path**: `apps/notifications/urls/urls.py:notification-mark-read` → `apps/notifications/views/views.py:NotificationViewSet.mark_read` → `apps/notifications/services/services.py:mark_notification_as_read`
- **Crosses**: Router → View → Service → DB update `notifications` (`is_read=True`).
- **Branches**:
  - Notification does not belong to user → Raises `NotFoundError` (HTTP 404).
  - Success → Updates `is_read=True` (HTTP 200).
- **Side effects**: DB update on `notifications`.

---

# 8. Search & Discovery Module (`apps/search`)

## GET `/api/search/projects/?q={query}`
- **Trigger**: HTTP GET search request for project marketplace listings.
- **Path**: `apps/search/urls/urls.py:search-projects` → `apps/search/views/views.py:ProjectSearchView.get` → `apps/search/documents/project.py:ProjectDocument.search()` → `apps/search/services/services.py:record_search_query`
- **Crosses**: Router → View → Elasticsearch 8 Cluster (`projects` index) → DB write `search_history` (Celery async).
- **Branches**:
  - Elasticsearch unreachable → Falls back to SQL `ILIKE` database query via `Project.objects.filter(...)`.
  - Success → Returns relevance-ranked and fuzzy-matched project results (HTTP 200).
- **Side effects**: Async record inserted into `search_history`, updates `search_suggestions` popularity counter.

---

## GET `/api/search/autocomplete/?q={term}`
- **Trigger**: HTTP GET request as user types into search inputs.
- **Path**: `apps/search/urls/urls.py:search-autocomplete` → `apps/search/views/views.py:AutocompleteView.get` → `SearchSuggestion.objects.filter(term__istartswith=q).order_by('-popularity')[:8]`
- **Crosses**: Router → View → Database read `search_suggestions`.
- **Branches**:
  - Query string length < 2 → Returns empty array `[]` (HTTP 200).
  - Success → Returns top suggestion terms (HTTP 200).
- **Side effects**: None (Read-only).

---

# 9. Background Jobs & Celery Queue Consumers

## `generate_ai_reports_sweep_task`
- **Trigger**: Scheduled by Celery Beat (e.g. every Monday at 00:00 UTC).
- **Path**: `apps/worklogs/tasks.py:generate_ai_reports_sweep_task` → queries active `ReportSchedule` and contracts with unbilled logs → calls `generate_ai_report_task.delay(contract_id, week_start, interval_days)`.
- **Crosses**: Celery Beat Scheduler → PostgreSQL query → Celery Task Dispatcher (`freelanceflow_default`).
- **Side effects**: Queues individual report generation jobs for all active contracts.

---

## `initialize_qdrant_collection_task`
- **Trigger**: Triggered via Django signal when a contract becomes `ACTIVE`.
- **Path**: `apps/worklogs/signals.py:post_save` → `apps/worklogs/tasks.py:initialize_qdrant_collection_task` → `apps/worklogs/services/qdrant_service.py:initialize_collection`
- **Crosses**: Django Signal → Celery Worker → PostgreSQL eager read → Google Gemini Embeddings API → Qdrant Vector Cloud API → DB write `qdrant_collections`.
- **Side effects**: Upserts 3072-dimensional scope embeddings to Qdrant Cloud, marks `QdrantCollection.is_initialized=True`.

---

## `process_razorpay_webhook_task`
- **Trigger**: Queued by `razorpay_webhook` view on payment events.
- **Path**: `apps/payments/tasks.py:process_razorpay_webhook_task` → `apps/payments/services/services.py:process_webhook_event`
- **Crosses**: Celery Worker (`freelanceflow_high_priority`) → DB write `payment_events` → DB write `payments` / `escrow`.
- **Branches**:
  - Event already processed → Exits immediately (Idempotent).
  - Event `payment.captured` → Marks payment captured, locks funds in escrow.
  - Event `payment.failed` → Marks payment failed, notifies client.
- **Side effects**: DB updates on payments and escrow records, customer notifications sent.

---

# 10. Architecture Integrity & Legacy Status

- **AI Services (`apps/worklogs/services/ai_service.py`)**: Unified across all endpoints (`/api/worklogs/ai/chat/`, `/api/worklogs/ai-chat/`, `/api/worklogs/deliverables/`). All AI requests execute through the 3-node LangGraph pipeline with Qdrant vector memory (Google Gemini 3072-dim embeddings), Groq LLaMA 3.3 70B (Primary) + Google Gemini 2.0 Flash (Fallback). Legacy `groq_service.py` is safely deleted.
- **Worklog Approvals (`apps/bidding/services/services_worklog_approval.py`)**: Harmonized with `apps/worklogs/services/services.py`. All approval and rejection events update canonical `WorkLog` status and audit fields (`client_notes`, `approved_at`, `approved_by`) atomically.

---

# 11. Real-Time Interaction & Workspace Navigation Flows

## Google OAuth Authentication Flow with Mode Differentiation
- **Trigger**: User clicks "Sign in with Google" (login mode) or "Sign up with Google" (register mode).
- **Path**: `frontend:AuthPage.jsx` → `GET /api/users/auth/google/init/?mode={login|register}` → Google OAuth Consent Screen → `GET /api/users/auth/google/callback/?code=...&state=...` → `apps/users/views/views_google_oauth.py:GoogleOAuthCallbackView`.
- **Branches**:
  - **Login Mode & User Not in DB**: Redirects to frontend `/auth/google/callback?error=please_signup_first&email=...` → Frontend auto-switches to Register tab, prefills email, and displays alert.
  - **Register Mode & User in DB**: Redirects with existing tokens or switches to login tab.
  - **Existing / Valid User**: Issues JWT access & refresh tokens and redirects to role dashboard (`/client/dashboard` or `/freelancer/browse`).

---

## Persistent In-App Notification Hub Flow
- **Trigger**: Sticky header `NotificationBell` mounted in `FreelancerLayout.jsx` and `ClientLayout.jsx`.
- **Path**: `GET /api/notifications/unread_count/` & `GET /api/notifications/` → `apps/notifications/views/views.py:NotificationViewSet`.
- **Actions**:
  - **Hover / Click**: Opens dropdown menu without layout shift.
  - **Mark One Read**: `POST /api/notifications/{id}/mark_read/` → `mark_notification_as_read`.
  - **Mark All Read**: `POST /api/notifications/mark_all_read/` → `mark_all_as_read`.

---

## WebSocket Bi-Directional Chat & Real-Time Read Receipts
- **Trigger**: Client or Freelancer enters conversation room `/ws/chat/{contract_id}/`.
- **Path**: `Daphne ASGI` → `apps/messaging/consumers.py:ChatConsumer`.
- **Execution Flow**:
  1. Sender sends message frame `{ type: "message", content: "..." }`.
  2. Consumer persists message in DB via `send_message(conversation_id, sender, content)` and broadcasts `type: "chat_message"` to room group.
  3. Recipient socket receives `chat_message`.
  4. If recipient is active in the room, consumer calls `_flush_unread_and_broadcast()` updating `Message.is_read=True` in DB.
  5. Consumer broadcasts `type: "read_receipt"` with `message_ids` to the room group.
  6. Sender socket receives `read_receipt` and flips message status from single tick (`✓`) to double blue tick (`✓✓`).

---

## AI Worklog Assistant Navigation & Qdrant Grounding
- **Trigger**: Freelancer clicks "Open AI Assistant" on any active contract from `/freelancer/worklogs`.
- **Path**: Client-side route `/freelancer/work/:contractId` (and `/freelancer/worklogs/:contractId`) under `<FreelancerLayout>` → `FreelancerWorkPage.jsx` → `GET /api/worklogs/ai/context/{contract_id}/`.
- **Context Grounding**: Fetches contract scope, active milestones, deliverables, past reports, and Qdrant vector memory collection status before opening real-time LangGraph assistant session.

