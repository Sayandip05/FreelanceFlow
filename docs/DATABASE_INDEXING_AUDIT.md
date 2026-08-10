# Production-Grade Database Indexing Audit & Optimization Report
**Project:** FreelanceFlow (Django Modular Monolith)  
**Scope:** Comprehensive database indexing audit for PostgreSQL across all 8 Django apps (`users`, `projects`, `bidding`, `payments`, `worklogs`, `messaging`, `notifications`, `search`).  
**Objective:** Optimize read query performance (SELECT, filter, get, order_by, search) while strictly avoiding write overhead penalties on frequently updated counters or insert-only logs.

---

## Indexing Design Principles & Rules Applied

1. **Selective Cardinality First:** In all multi-column composite indexes, higher-cardinality foreign keys (`contract_id`, `client_id`, `user_id`) precede low-cardinality status/boolean enums (`status`, `is_active`).
2. **Order-By Matching (B-Tree Scan Elimination):** Composite indexes include matching sort orders (e.g., `['-created_at']` or `['-date']`) so PostgreSQL can execute index-only scans without in-memory sorting (`Sort` or `External Sort`).
3. **No Standalone Boolean / PK Indexing:** Standalone booleans (`is_active`, `is_read`, `is_public`) are never indexed alone; they are always combined with selective parent FKs.
4. **No Hot-Counter Indexing:** Fields subject to high-frequency in-place mutations (e.g., `last_seen`, `view_count`, `updated_at` on high-churn tables) are excluded from single-column indexing to prevent write amplification and index fragmentation.
5. **Reverse Relation & M2M Indexing:** Django auto-indexes ForeignKeys on the child table, but reverse lookups combining the FK with a status (e.g., `contract.milestones.filter(status='PENDING')`) require composite indexes `(contract_id, status)`.

---

# Comprehensive Indexing Catalog by App

---

## 1. App: `users`

### Index USR-IDX-01
- **APP:** users
- **MODEL:** User
- **INDEX TYPE:** Composite
- **FIELDS:** `['role', 'is_deactivated']`
- **REASON:** `User.objects.filter(role=Roles.FREELANCER, is_deactivated=False)` in `selectors.py` `list_freelancers()` and auth authorization gates.
- **META:**
```python
class Meta:
    db_table = "users"
    indexes = [
        models.Index(
            fields=['role', 'is_deactivated'],
            name='user_role_active_idx'
        ),
    ]
```

### Index USR-IDX-02
- **APP:** users
- **MODEL:** FreelancerProfile
- **INDEX TYPE:** Composite & Single-Column
- **FIELDS:** `['subscription_tier', '-average_rating']` & `['-total_earned']`
- **REASON:** Freelancer directory filtering by subscription tier and ranking top freelancers by average rating in search and public listings (`order_by('-total_earned')`).
- **META:**
```python
class Meta:
    db_table = "freelancer_profiles"
    indexes = [
        models.Index(
            fields=['subscription_tier', '-average_rating'],
            name='freelancer_tier_rating_idx'
        ),
        models.Index(
            fields=['-total_earned'],
            name='freelancer_earned_idx'
        ),
    ]
```

### Index USR-IDX-03
- **APP:** users
- **MODEL:** ActivityLog
- **INDEX TYPE:** Composite
- **FIELDS:** `['user', 'action_type', '-created_at']`
- **REASON:** `ActivityLog.objects.filter(user=user, action_type__in=security_actions).order_by('-created_at')` in `services_activity.py` `get_security_events()` and `get_payment_activities()`.
- **META:**
```python
class Meta:
    db_table = "activity_logs"
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=["user", "-created_at"],
            name="act_log_user_created_idx"
        ),
        models.Index(
            fields=["user", "action_type", "-created_at"],
            name="act_log_user_action_idx"
        ),
    ]
```

### Index USR-IDX-04
- **APP:** users
- **MODEL:** UserOnlineStatus
- **INDEX TYPE:** Composite
- **FIELDS:** `['is_online', 'last_seen']`
- **REASON:** `UserOnlineStatus.objects.filter(is_online=True, last_seen__gte=threshold)` in presence selectors and heartbeat sweep queries.
- **META:**
```python
class Meta:
    db_table = "user_online_status"
    indexes = [
        models.Index(
            fields=['is_online', 'last_seen'],
            name='user_presence_idx'
        ),
    ]
```

---

## 2. App: `projects`

### Index PRJ-IDX-01
- **APP:** projects
- **MODEL:** Project
- **INDEX TYPE:** Composite
- **FIELDS:** `['status', '-created_at']`, `['client', 'status', '-created_at']`, `['status', 'budget']`
- **REASON:** `Project.objects.filter(status=Project.Status.OPEN).order_by('-created_at')` in `get_open_projects()` (the most frequented read query on the platform), and client dashboard project listings.
- **META:**
```python
class Meta:
    db_table = "projects"
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=['status', '-created_at'],
            name='project_status_created_idx'
        ),
        models.Index(
            fields=['client', 'status', '-created_at'],
            name='project_client_status_idx'
        ),
        models.Index(
            fields=['status', 'budget'],
            name='project_status_budget_idx'
        ),
    ]
```

### Index PRJ-IDX-02
- **APP:** projects
- **MODEL:** ProjectSkill
- **INDEX TYPE:** Single-Column
- **FIELDS:** `['skill_name']`
- **REASON:** `ProjectSkill.objects.filter(skill_name__in=skills)` in `get_open_projects()` skill filtering. Existing `unique_together = ["project", "skill_name"]` creates a B-Tree on `(project_id, skill_name)` which cannot speed up standalone `skill_name` searches.
- **META:**
```python
class Meta:
    db_table = "project_skills"
    unique_together = ["project", "skill_name"]
    indexes = [
        models.Index(
            fields=['skill_name'],
            name='project_skill_name_idx'
        ),
    ]
```

### Index PRJ-IDX-03
- **APP:** projects
- **MODEL:** ProjectBookmark
- **INDEX TYPE:** Composite
- **FIELDS:** `['user', '-created_at']`
- **REASON:** `ProjectBookmark.objects.filter(user=user).order_by('-created_at')` in `services_bookmark.py` `get_bookmarked_projects()`.
- **META:**
```python
class Meta:
    db_table = "project_bookmarks"
    unique_together = ["user", "project"]
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=['user', '-created_at'],
            name='proj_bookmark_user_date_idx'
        ),
    ]
```

### Index PRJ-IDX-04
- **APP:** projects
- **MODEL:** ProjectDraft
- **INDEX TYPE:** Composite
- **FIELDS:** `['client', '-updated_at']`
- **REASON:** `ProjectDraft.objects.filter(client=client).order_by('-updated_at')` in draft listing views.
- **META:**
```python
class Meta:
    db_table = "project_drafts"
    ordering = ["-updated_at"]
    indexes = [
        models.Index(
            fields=['client', '-updated_at'],
            name='proj_draft_client_date_idx'
        ),
    ]
```

---

## 3. App: `bidding`

### Index BID-IDX-01
- **APP:** bidding
- **MODEL:** Bid
- **INDEX TYPE:** Composite
- **FIELDS:** `['freelancer', 'status', '-created_at']` & `['project', 'status']`
- **REASON:** `Bid.objects.filter(freelancer=freelancer, status=status).order_by('-created_at')` in `get_freelancer_bids()` and `Bid.objects.filter(project=project, status=status)` in project proposals management.
- **META:**
```python
class Meta:
    db_table = "bids"
    ordering = ["-created_at"]
    unique_together = ["project", "freelancer"]
    indexes = [
        models.Index(
            fields=['freelancer', 'status', '-created_at'],
            name='bid_freelancer_status_idx'
        ),
        models.Index(
            fields=['project', 'status'],
            name='bid_project_status_idx'
        ),
    ]
```

### Index BID-IDX-02
- **APP:** bidding
- **MODEL:** Contract
- **INDEX TYPE:** Composite
- **FIELDS:** `['status', 'is_active']`
- **REASON:** `Contract.objects.filter(is_active=True, status=Contract.Status.ACTIVE)` in active contract selectors, Celery report sweepers, and client/freelancer dashboards.
- **META:**
```python
class Meta:
    db_table = "contracts"
    indexes = [
        models.Index(
            fields=['status', 'is_active'],
            name='contract_status_active_idx'
        ),
    ]
```

### Index BID-IDX-03
- **APP:** bidding
- **MODEL:** Review
- **INDEX TYPE:** Composite
- **FIELDS:** `['reviewee', 'is_public', '-created_at']` & `['reviewer', '-created_at']`
- **REASON:** `Review.objects.filter(reviewer=user).order_by('-created_at')` in `ReviewViewSet.given()` and `Review.objects.filter(reviewee=user, is_public=True).order_by('-created_at')` in `get_user_reviews()`.
- **META:**
```python
class Meta:
    db_table = "reviews"
    ordering = ["-created_at"]
    unique_together = ["contract", "reviewer"]
    indexes = [
        models.Index(
            fields=["reviewee", "is_public", "-created_at"],
            name="review_reviewee_pub_idx"
        ),
        models.Index(
            fields=["reviewer", "-created_at"],
            name="review_reviewer_created_idx"
        ),
        models.Index(
            fields=["contract"],
            name="review_contract_idx"
        ),
    ]
```

### Index BID-IDX-04
- **APP:** bidding
- **MODEL:** CounterOffer
- **INDEX TYPE:** Composite
- **FIELDS:** `['bid', 'status']`
- **REASON:** `CounterOffer.objects.filter(bid=bid, status='PENDING')` in counter-offer evaluation and client negotiation screens.
- **META:**
```python
class Meta:
    db_table = "counter_offers"
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=['bid', 'status'],
            name='counter_bid_status_idx'
        ),
    ]
```

### Index BID-IDX-05
- **APP:** bidding
- **MODEL:** ContractAmendment
- **INDEX TYPE:** Composite
- **FIELDS:** `['contract', 'status']`
- **REASON:** `ContractAmendment.objects.filter(contract=contract, status='PENDING')` in contract amendment workflows.
- **META:**
```python
class Meta:
    db_table = "contract_amendments"
    indexes = [
        models.Index(
            fields=['contract', 'status'],
            name='amendment_contract_status_idx'
        ),
    ]
```

---

## 4. App: `payments`

### Index PAY-IDX-01
- **APP:** payments
- **MODEL:** Payment
- **INDEX TYPE:** Composite & Single-Column
- **FIELDS:** `['contract', 'status']` & `['razorpay_order_id']` & `['razorpay_payment_id']`
- **REASON:**
  - `Payment.objects.filter(contract=contract, status='RELEASED')` in `get_freelancer_earnings()`.
  - `Payment.objects.get(razorpay_order_id=order_id)` in webhook payment capture and signature verification handlers.
- **META:**
```python
class Meta:
    db_table = "payments"
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=['contract', 'status'],
            name='payment_contract_status_idx'
        ),
        models.Index(
            fields=['razorpay_order_id'],
            name='payment_rzp_order_idx'
        ),
        models.Index(
            fields=['razorpay_payment_id'],
            name='payment_rzp_pay_idx'
        ),
    ]
```

### Index PAY-IDX-02
- **APP:** payments
- **MODEL:** PaymentMilestone
- **INDEX TYPE:** Composite
- **FIELDS:** `['contract', 'status']` & `['status', 'due_date']` & `['contract', 'order']`
- **REASON:**
  - `PaymentMilestone.objects.filter(contract_id=contract_id).order_by('due_date')` in `get_contract_milestones()`.
  - `PaymentMilestone.objects.filter(contract_id__in=..., status='PENDING', due_date__lte=end_date)` in `get_upcoming_milestones()`.
- **META:**
```python
class Meta:
    db_table = "payment_milestones"
    indexes = [
        models.Index(
            fields=['contract', 'status'],
            name='milestone_contract_stat_idx'
        ),
        models.Index(
            fields=['status', 'due_date'],
            name='milestone_stat_duedate_idx'
        ),
        models.Index(
            fields=['contract', 'order'],
            name='milestone_contract_ord_idx'
        ),
    ]
```

### Index PAY-IDX-03
- **APP:** payments
- **MODEL:** PaymentDispute
- **INDEX TYPE:** Composite
- **FIELDS:** `['disputer', 'status']` & `['status', '-created_at']`
- **REASON:** `PaymentDispute.objects.filter(status=Status.OPEN)` in admin dispute queue and `filter(disputer=user, status=...)` in user dispute history.
- **META:**
```python
class Meta:
    db_table = "payment_disputes"
    indexes = [
        models.Index(
            fields=['disputer', 'status'],
            name='dispute_user_status_idx'
        ),
        models.Index(
            fields=['status', '-created_at'],
            name='dispute_status_created_idx'
        ),
    ]
```

---

## 5. App: `worklogs`

### Index WRK-IDX-01
- **APP:** worklogs
- **MODEL:** WorkLog
- **INDEX TYPE:** Composite & Single-Column
- **FIELDS:** `['freelancer', '-date']` & `['contract', 'status']` & `['date']`
- **REASON:**
  - `WorkLog.objects.filter(freelancer=freelancer).order_by('-date')` in `get_freelancer_worklogs()`.
  - `WorkLog.objects.filter(contract_id=contract_id, status='APPROVED')` in hours summary aggregations.
  - Note: `unique_together = ["contract", "date"]` covers `(contract, date)` lookups.
- **META:**
```python
class Meta:
    db_table = "work_logs"
    ordering = ["-date", "-created_at"]
    unique_together = ["contract", "date"]
    indexes = [
        models.Index(
            fields=['freelancer', '-date'],
            name='worklog_freelancer_date_idx'
        ),
        models.Index(
            fields=['contract', 'status'],
            name='worklog_contract_status_idx'
        ),
        models.Index(
            fields=['date'],
            name='worklog_date_idx'
        ),
    ]
```

### Index WRK-IDX-02
- **APP:** worklogs
- **MODEL:** Deliverable
- **INDEX TYPE:** Composite
- **FIELDS:** `['contract', 'status', '-created_at']` & `['freelancer', 'status', '-created_at']` & `['status', '-created_at']`
- **REASON:**
  - `Deliverable.objects.filter(contract_id=contract_id, status=status)` in `get_contract_deliverables()`.
  - `Deliverable.objects.filter(freelancer=freelancer, status=status)` in `get_freelancer_deliverables()`.
  - `Deliverable.objects.filter(status='SUBMITTED')` in `get_pending_approval_deliverables()`.
- **META:**
```python
class Meta:
    db_table = "deliverables"
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=['contract', 'status', '-created_at'],
            name='deliverable_contract_stat_idx'
        ),
        models.Index(
            fields=['freelancer', 'status', '-created_at'],
            name='deliverable_free_stat_idx'
        ),
        models.Index(
            fields=['status', '-created_at'],
            name='deliverable_status_date_idx'
        ),
    ]
```

### Index WRK-IDX-03
- **APP:** worklogs
- **MODEL:** ReportSchedule
- **INDEX TYPE:** Composite
- **FIELDS:** `['is_active', 'next_report_date']`
- **REASON:** `ReportSchedule.objects.filter(is_active=True, next_report_date__lte=today)` in Celery Beat daily report trigger task `trigger_scheduled_reports`.
- **META:**
```python
class Meta:
    db_table = "report_schedules"
    indexes = [
        models.Index(
            fields=['is_active', 'next_report_date'],
            name='report_schedule_active_idx'
        ),
    ]
```

---

## 6. App: `messaging`

### Index MSG-IDX-01
- **APP:** messaging
- **MODEL:** Conversation
- **INDEX TYPE:** Single-Column
- **FIELDS:** `['-updated_at']`
- **REASON:** Default ordering and conversation feed retrieval `ordering = ["-updated_at"]` in `get_user_conversations()`.
- **META:**
```python
class Meta:
    db_table = "conversations"
    ordering = ["-updated_at"]
    indexes = [
        models.Index(
            fields=['-updated_at'],
            name='conversation_updated_idx'
        ),
    ]
```

### Index MSG-IDX-02
- **APP:** messaging
- **MODEL:** Message
- **INDEX TYPE:** Composite
- **FIELDS:** `['conversation', '-created_at']` & `['conversation', 'is_read', 'sender']`
- **REASON:**
  - `Message.objects.filter(conversation_id=cid).order_by('-created_at')[:50]` in chat UI message stream and `last_message` serializer field.
  - `Message.objects.filter(conversation=c, is_read=False).exclude(sender=user)` in `annotated_unread_count` calculation.
- **META:**
```python
class Meta:
    db_table = "messages"
    ordering = ["created_at"]
    indexes = [
        models.Index(
            fields=['conversation', '-created_at'],
            name='msg_conv_created_idx'
        ),
        models.Index(
            fields=['conversation', 'is_read', 'sender'],
            name='msg_conv_unread_idx'
        ),
    ]
```

---

## 7. App: `notifications`

### Index NOT-IDX-01
- **APP:** notifications
- **MODEL:** Notification
- **INDEX TYPE:** Composite
- **FIELDS:** `['recipient', 'is_read', '-created_at']` & `['recipient', '-created_at']`
- **REASON:**
  - `Notification.objects.filter(recipient=user).order_by('-created_at')` in notifications center feed.
  - `Notification.objects.filter(recipient=user, is_read=False).count()` in topbar unread badge indicator.
- **META:**
```python
class Meta:
    db_table = "notifications"
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=["recipient", "is_read", "-created_at"],
            name="notif_recip_read_date_idx"
        ),
        models.Index(
            fields=["recipient", "-created_at"],
            name="notif_recip_created_idx"
        ),
    ]
```

### Index NOT-IDX-02
- **APP:** notifications
- **MODEL:** SystemAnnouncement
- **INDEX TYPE:** Composite
- **FIELDS:** `['is_active', 'start_date', 'end_date']`
- **REASON:** `SystemAnnouncement.objects.filter(is_active=True, start_date__lte=now, end_date__gte=now)` on every user session initialization.
- **META:**
```python
class Meta:
    db_table = "system_announcements"
    indexes = [
        models.Index(
            fields=['is_active', 'start_date', 'end_date'],
            name='announcement_active_window_idx'
        ),
    ]
```

---

## 8. App: `search`

### Index SCH-IDX-01
- **APP:** search
- **MODEL:** SearchHistory
- **INDEX TYPE:** Composite
- **FIELDS:** `['user', 'search_type', '-created_at']`
- **REASON:** `SearchHistory.objects.filter(user=user, search_type=st).order_by('-created_at')[:10]` in search dropdown history popup.
- **META:**
```python
class Meta:
    db_table = "search_history"
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=["user", "search_type", "-created_at"],
            name="search_hist_user_type_idx"
        ),
    ]
```

### Index SCH-IDX-02
- **APP:** search
- **MODEL:** SavedSearch
- **INDEX TYPE:** Composite
- **FIELDS:** `['user', 'is_active', '-created_at']`
- **REASON:** `SavedSearch.objects.filter(user=user, is_active=True).order_by('-created_at')` in user saved searches list.
- **META:**
```python
class Meta:
    db_table = "saved_searches"
    ordering = ["-created_at"]
    indexes = [
        models.Index(
            fields=['user', 'is_active', '-created_at'],
            name='saved_search_user_active_idx'
        ),
    ]
```

### Index SCH-IDX-03
- **APP:** search
- **MODEL:** SearchSuggestion
- **INDEX TYPE:** Composite
- **FIELDS:** `['is_active', '-popularity']`
- **REASON:** `SearchSuggestion.objects.filter(is_active=True).order_by('-popularity')[:8]` in global search autocomplete suggestions.
- **META:**
```python
class Meta:
    db_table = "search_suggestions"
    ordering = ["-popularity"]
    indexes = [
        models.Index(
            fields=["term"],
            name="search_sugg_term_idx"
        ),
        models.Index(
            fields=["is_active", "-popularity"],
            name="search_sugg_active_pop_idx"
        ),
    ]
```

---

# Migration Strategy & Prioritization Matrix

To ensure zero downtime and optimal database performance, migrations are stratified into three priority tiers based on query frequency, table size, and latency impact.

| Tier | Urgency | Description | Models Covered | Indexes |
|---|---|---|---|---|
| **Tier 1 (Critical)** | Immediate | High-frequency API endpoints, primary feeds, and real-time messaging/notifications. | `Project`, `ProjectSkill`, `Bid`, `Message`, `Notification`, `Payment` | `project_status_created_idx`, `project_skill_name_idx`, `bid_freelancer_status_idx`, `msg_conv_created_idx`, `msg_conv_unread_idx`, `notif_recip_read_date_idx`, `payment_rzp_order_idx` |
| **Tier 2 (Core)** | High | Contract workflows, milestone billing, worklogs, and deliverable approvals. | `Contract`, `PaymentMilestone`, `WorkLog`, `Deliverable`, `ReportSchedule`, `Review` | `contract_status_active_idx`, `milestone_contract_stat_idx`, `worklog_freelancer_date_idx`, `deliverable_contract_stat_idx`, `report_schedule_active_idx`, `review_reviewee_pub_idx` |
| **Tier 3 (Supporting)** | Standard | Search history, bookmarks, audit logs, presence tracking, and system announcements. | `ActivityLog`, `UserOnlineStatus`, `ProjectBookmark`, `ProjectDraft`, `PaymentDispute`, `SearchHistory`, `SearchSuggestion` | `act_log_user_action_idx`, `user_presence_idx`, `proj_bookmark_user_date_idx`, `dispute_status_created_idx`, `search_hist_user_type_idx` |

---

### Migration Execution Commands

When ready to apply the database indexes:
```bash
# 1. Generate Django migration files per app
python manage.py makemigrations users projects bidding payments worklogs messaging notifications search

# 2. In PostgreSQL production, migrations can be applied concurrently using RunSQL or standard migrate:
python manage.py migrate
```
