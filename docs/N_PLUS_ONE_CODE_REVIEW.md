# Production-Grade N+1 Query Audit & Optimization Report
**Project:** FreelanceFlow (Modular Monolith)  
**Scope:** Exhaustive audit across all 8 Django apps (`users`, `projects`, `bidding`, `payments`, `worklogs`, `messaging`, `notifications`, `search`).  
**Audit Target Layers:** `models.py` → `selectors.py` → `services.py` → `views.py` → `serializers.py` → `tasks.py`

---

## Executive Summary

This code review focuses on database query efficiency across all 8 domain modules of the FreelanceFlow backend. We scanned for:
1. Unprefetched ForeignKeys and reverse OneToOne relations in querysets rendered by nested serializers.
2. ORM queries executed inside `SerializerMethodField` or `to_representation()` methods for each item in a collection.
3. Python-level loops that trigger sequential database queries instead of database-level batch queries or annotations (`Count`, `Sum`, `Exists`).
4. Multi-hop relation chains (e.g., `contract.bid.project.client.client_profile`) traversed without eager loading.
5. Celery tasks and background sweeps iterating through querysets with unoptimized per-iteration database hits.

---

## Table of Contents
1. [App 1: `apps/users`](#1-appsusers)
2. [App 2: `apps/projects`](#2-appsprojects)
3. [App 3: `apps/bidding`](#3-appsbidding)
4. [App 4: `apps/payments`](#4-appspayments)
5. [App 5: `apps/worklogs`](#5-appsworklogs)
6. [App 6: `apps/messaging`](#6-appsmessaging)
7. [App 7: `apps/notifications`](#7-appsnotifications)
8. [App 8: `apps/search`](#8-appssearch)
9. [Architecture Best Practices & Summary Matrix](#9-architecture-best-practices--summary-matrix)

---

## 1. `apps/users`

---

### Issue USR-01: Reverse OneToOne Profile Access in `UserSerializer`
- **FILE:** `apps/users/views/views.py`
- **FUNCTION:** `UserDetailView`
- **PROBLEM:** `UserDetailView.queryset = User.objects.all()`. When `UserSerializer` serializes the user, it evaluates `freelancer_profile` and `client_profile` (both reverse OneToOne relations). Without `select_related`, each lookup executes 2 additional SQL queries.
- **PROBLEMATIC CODE:**
  ```python
  class UserDetailView(generics.RetrieveAPIView):
      queryset = User.objects.all()
      serializer_class = UserSerializer
  ```
- **WHY IT CAUSES N+1:** Accessing `user.freelancer_profile` and `user.client_profile` in DRF serializers generates separate `SELECT` queries for each profile relation if not prefetched.
- **FIX:**
  ```python
  class UserDetailView(generics.RetrieveAPIView):
      queryset = User.objects.select_related('freelancer_profile', 'client_profile').all()
      serializer_class = UserSerializer
  ```

---

### Issue USR-02: User Email Traversal in Activity Logs
- **FILE:** `apps/users/services/services_activity.py`
- **FUNCTION:** `get_user_activity_log()`, `get_security_events()`, `get_payment_activities()`
- **PROBLEM:** `ActivityLogSerializer` defines `user_email = serializers.EmailField(source='user.email')`. When `ActivityLogViewSet` lists activity logs using `get_user_activity_log(self.request.user, limit=100)`, each record accesses `log.user.email` without `select_related('user')`.
- **PROBLEMATIC CODE:**
  ```python
  def get_user_activity_log(user, limit=50, action=None, resource_type=None):
      queryset = ActivityLog.objects.filter(user=user)
      if action:
          queryset = queryset.filter(action=action)
      if resource_type:
          queryset = queryset.filter(resource_type=resource_type)
      return queryset.order_by('-created_at')[:limit]
  ```
- **WHY IT CAUSES N+1:** For a list of 100 activity logs, DRF resolves `log.user.email` 100 times, resulting in 100 duplicate queries.
- **FIX:**
  ```python
  def get_user_activity_log(user, limit=50, action=None, resource_type=None):
      queryset = ActivityLog.objects.filter(user=user).select_related('user')
      if action:
          queryset = queryset.filter(action=action)
      if resource_type:
          queryset = queryset.filter(resource_type=resource_type)
      return queryset.order_by('-created_at')[:limit]
  ```

---

## 2. `apps/projects`

---

### Issue PRJ-01: Nested User Profiles in Project Serializer
- **FILE:** `apps/projects/selectors.py`
- **FUNCTION:** `get_open_projects()` and `get_client_projects()`
- **PROBLEM:** Both selectors execute `.select_related('client').prefetch_related('skills')`. However, `ProjectListSerializer` and `ProjectDetailSerializer` use `client = UserSerializer(read_only=True)`. `UserSerializer` loads `client.client_profile` and `client.freelancer_profile`.
- **PROBLEMATIC CODE:**
  ```python
  # apps/projects/selectors.py
  def get_open_projects(budget_min=None, budget_max=None, skills=None, search=None):
      queryset = Project.objects.filter(
          status=Project.Status.OPEN
      ).select_related('client').prefetch_related('skills')
      ...
      return queryset
  ```
- **WHY IT CAUSES N+1:** For 50 open projects, `select_related('client')` joins the `User` table, but accessing `client.client_profile` and `client.freelancer_profile` executes 2 separate queries per project ($50 \times 2 = 100$ extra queries).
- **FIX:**
  ```python
  def get_open_projects(budget_min=None, budget_max=None, skills=None, search=None):
      queryset = Project.objects.filter(
          status=Project.Status.OPEN
      ).select_related(
          'client',
          'client__client_profile',
          'client__freelancer_profile'
      ).prefetch_related('skills')
      ...
      return queryset

  def get_client_projects(client):
      return Project.objects.filter(
          client=client
      ).select_related(
          'client',
          'client__client_profile',
          'client__freelancer_profile'
      ).prefetch_related('skills')
  ```

---

### Issue PRJ-02: Project Client Traversal in Bookmarks List
- **FILE:** `apps/projects/services/services_bookmark.py`
- **FUNCTION:** `get_bookmarked_projects()`
- **PROBLEM:** `get_bookmarked_projects` only does `.select_related('project')`. However, `ProjectBookmarkSerializer` specifies `client_email = serializers.EmailField(source='project.client.email', read_only=True)`.
- **PROBLEMATIC CODE:**
  ```python
  def get_bookmarked_projects(user):
      """Get user's bookmarked projects"""
      return ProjectBookmark.objects.filter(user=user).select_related('project')
  ```
- **WHY IT CAUSES N+1:** Serializing each bookmark accesses `bookmark.project.client`, which is not selected, generating an individual SQL query for each bookmark.
- **FIX:**
  ```python
  def get_bookmarked_projects(user):
      """Get user's bookmarked projects"""
      return ProjectBookmark.objects.filter(user=user).select_related('project__client')
  ```

---

### Issue PRJ-03: Missing Nested Client Profiles on Project Bids Action
- **FILE:** `apps/projects/views/views.py`
- **FUNCTION:** `ProjectViewSet.bids()`
- **PROBLEM:** In `ProjectViewSet.bids()`, the queryset selects `freelancer`, `freelancer__freelancer_profile`, `freelancer__client_profile`, `project`, `project__client`, and prefetches `project__skills`. But `BidListSerializer` includes `project = ProjectListSerializer(read_only=True)`, which serializes `project.client` with `UserSerializer` requiring `project__client__client_profile` and `project__client__freelancer_profile`.
- **PROBLEMATIC CODE:**
  ```python
  bids = project.bids.all().select_related(
      'freelancer', 
      'freelancer__freelancer_profile', 
      'freelancer__client_profile', 
      'project', 
      'project__client'
  ).prefetch_related('project__skills')
  ```
- **WHY IT CAUSES N+1:** DRF's `UserSerializer` on `project.client` triggers 2 database queries for every bid on the project.
- **FIX:**
  ```python
  bids = project.bids.all().select_related(
      'freelancer', 
      'freelancer__freelancer_profile', 
      'freelancer__client_profile', 
      'project', 
      'project__client',
      'project__client__client_profile',
      'project__client__freelancer_profile',
  ).prefetch_related('project__skills')
  ```

---

## 3. `apps/bidding`

---

### Issue BID-01: Incomplete Relation Chain in `BidViewSet.get_queryset()`
- **FILE:** `apps/bidding/views/views.py`
- **FUNCTION:** `BidViewSet.get_queryset()`
- **PROBLEM:** For client users, `BidViewSet.get_queryset()` runs:
  `Bid.objects.filter(project__client=user).select_related('freelancer', 'project')`
- **PROBLEMATIC CODE:**
  ```python
  def get_queryset(self):
      user = self.request.user
      if user.role == 'FREELANCER':
          return get_freelancer_bids(user)
      
      # For clients, return bids on their projects
      return Bid.objects.filter(
          project__client=user
      ).select_related('freelancer', 'project')
  ```
- **WHY IT CAUSES N+1:** `BidListSerializer` serializes:
  1. `freelancer` (`UserSerializer` → requires `freelancer__freelancer_profile`, `freelancer__client_profile`)
  2. `project` (`ProjectListSerializer` → requires `project__client`, `project__client__client_profile`, `project__client__freelancer_profile`, and `project__skills`)
  This results in up to 5 extra SQL queries per bid item.
- **FIX:**
  ```python
  def get_queryset(self):
      user = self.request.user
      if user.role == 'FREELANCER':
          return get_freelancer_bids(user)
      
      return Bid.objects.filter(
          project__client=user
      ).select_related(
          'freelancer',
          'freelancer__freelancer_profile',
          'freelancer__client_profile',
          'project',
          'project__client',
          'project__client__client_profile',
          'project__client__freelancer_profile',
      ).prefetch_related('project__skills')
  ```

---

### Issue BID-02: Missing Multi-Hop Relations in Contract Selectors
- **FILE:** `apps/bidding/selectors.py`
- **FUNCTION:** `get_freelancer_active_contracts()` and `get_client_active_contracts()`
- **PROBLEM:** Selectors only use `.select_related('bid__project', 'bid__freelancer')`. When `ContractSerializer` is serialized, it accesses:
  - `contract.bid.project.client` (UserSerializer)
  - `contract.bid.freelancer` (UserSerializer)
  - `contract.bid.project.skills` (ProjectSkillSerializer)
- **PROBLEMATIC CODE:**
  ```python
  def get_freelancer_active_contracts(freelancer) -> QuerySet[Contract]:
      return Contract.objects.filter(
          bid__freelancer=freelancer,
          is_active=True
      ).select_related('bid__project', 'bid__freelancer')

  def get_client_active_contracts(client) -> QuerySet[Contract]:
      return Contract.objects.filter(
          bid__project__client=client,
          is_active=True
      ).select_related('bid__project', 'bid__freelancer')
  ```
- **WHY IT CAUSES N+1:** Each contract triggers queries for `bid.project.client`, `client_profile`, `freelancer_profile`, and `skills.all()`.
- **FIX:**
  ```python
  def get_freelancer_active_contracts(freelancer) -> QuerySet[Contract]:
      return Contract.objects.filter(
          bid__freelancer=freelancer,
          is_active=True
      ).select_related(
          'bid__project',
          'bid__project__client',
          'bid__project__client__client_profile',
          'bid__project__client__freelancer_profile',
          'bid__freelancer',
          'bid__freelancer__freelancer_profile',
          'bid__freelancer__client_profile',
      ).prefetch_related('bid__project__skills')

  def get_client_active_contracts(client) -> QuerySet[Contract]:
      return Contract.objects.filter(
          bid__project__client=client,
          is_active=True
      ).select_related(
          'bid__project',
          'bid__project__client',
          'bid__project__client__client_profile',
          'bid__project__client__freelancer_profile',
          'bid__freelancer',
          'bid__freelancer__freelancer_profile',
          'bid__freelancer__client_profile',
      ).prefetch_related('bid__project__skills')
  ```

---

### Issue BID-03: Review Profile Serialization N+1
- **FILE:** `apps/bidding/services/services_review.py` & `apps/bidding/views/views_review.py`
- **FUNCTION:** `get_user_reviews()`, `ReviewViewSet.get_queryset()`, `ReviewViewSet.given()`
- **PROBLEM:** `ReviewSerializer` serializes both `reviewer = UserSerializer(read_only=True)` and `reviewee = UserSerializer(read_only=True)`. The querysets only select `reviewer`, `reviewee`, `contract` without their profiles.
- **PROBLEMATIC CODE:**
  ```python
  # apps/bidding/services/services_review.py
  def get_user_reviews(user: User, is_public_only: bool = True):
      queryset = Review.objects.filter(reviewee=user).select_related(
          'reviewer', 'contract'
      )
      ...
  ```
- **WHY IT CAUSES N+1:** For each review, 4 extra queries are executed: `reviewer.freelancer_profile`, `reviewer.client_profile`, `reviewee.freelancer_profile`, and `reviewee.client_profile`.
- **FIX:**
  ```python
  def get_user_reviews(user: User, is_public_only: bool = True):
      queryset = Review.objects.filter(reviewee=user).select_related(
          'reviewer',
          'reviewer__freelancer_profile',
          'reviewer__client_profile',
          'reviewee',
          'reviewee__freelancer_profile',
          'reviewee__client_profile',
          'contract',
          'contract__bid__project',
      )
      if is_public_only:
          queryset = queryset.filter(is_public=True)
      return queryset
  ```

---

### Issue BID-04: Retraction Detail Missing Project Relation
- **FILE:** `apps/bidding/services/services_retraction.py`
- **FUNCTION:** `get_retraction_details()`
- **PROBLEM:** `retraction = BidRetraction.objects.select_related('bid').get(bid_id=bid_id)` is fetched, but then `'project_title': retraction.bid.project.title` is accessed.
- **PROBLEMATIC CODE:**
  ```python
  def get_retraction_details(bid_id):
      try:
          retraction = BidRetraction.objects.select_related('bid').get(bid_id=bid_id)
          return {
              'bid_id': retraction.bid_id,
              'reason': retraction.reason,
              'retracted_at': retraction.retracted_at,
              'bid_amount': retraction.bid.amount,
              'project_title': retraction.bid.project.title
          }
      except BidRetraction.DoesNotExist:
          return None
  ```
- **WHY IT CAUSES N+1:** `select_related('bid')` does not fetch `project`, resulting in an extra DB query when accessing `retraction.bid.project.title`.
- **FIX:**
  ```python
  def get_retraction_details(bid_id):
      try:
          retraction = BidRetraction.objects.select_related('bid__project').get(bid_id=bid_id)
          return {
              'bid_id': retraction.bid_id,
              'reason': retraction.reason,
              'retracted_at': retraction.retracted_at,
              'bid_amount': retraction.bid.amount,
              'project_title': retraction.bid.project.title
          }
      except BidRetraction.DoesNotExist:
          return None
  ```

---

## 4. `apps/payments`

---

### Issue PAY-01: Payment History Missing Freelancer & Client Relationships
- **FILE:** `apps/payments/selectors.py`
- **FUNCTION:** `get_client_payment_history()` and `get_freelancer_earnings()`
- **PROBLEM:** `PaymentListSerializer` specifies:
  - `freelancer_name = serializers.CharField(source='contract.bid.freelancer.full_name')`
  - `client_name = serializers.CharField(source='contract.bid.project.client.full_name')`
  - `project_title = serializers.CharField(source='contract.bid.project.title')`
  `get_client_payment_history` only does `.select_related('contract__bid__project')`.
- **PROBLEMATIC CODE:**
  ```python
  def get_client_payment_history(client) -> QuerySet[Payment]:
      return Payment.objects.filter(
          contract__bid__project__client=client
      ).select_related('contract__bid__project')

  def get_freelancer_earnings(freelancer) -> QuerySet[Payment]:
      return Payment.objects.filter(
          contract__bid__freelancer=freelancer,
          status=Payment.Status.RELEASED
      ).select_related('contract__bid__project')
  ```
- **WHY IT CAUSES N+1:** When serializing payments, accessing `contract.bid.freelancer` and `contract.bid.project.client` fires 2 database queries per row.
- **FIX:**
  ```python
  def get_client_payment_history(client) -> QuerySet[Payment]:
      return Payment.objects.filter(
          contract__bid__project__client=client
      ).select_related(
          'contract__bid__project',
          'contract__bid__project__client',
          'contract__bid__freelancer'
      )

  def get_freelancer_earnings(freelancer) -> QuerySet[Payment]:
      return Payment.objects.filter(
          contract__bid__freelancer=freelancer,
          status=Payment.Status.RELEASED
      ).select_related(
          'contract__bid__project',
          'contract__bid__project__client',
          'contract__bid__freelancer'
      )
  ```

---

### Issue PAY-02: Payment Milestones Missing Contract & Project Relations
- **FILE:** `apps/payments/services/services_milestone.py`
- **FUNCTION:** `get_contract_milestones()` and `get_upcoming_milestones()`
- **PROBLEM:** `PaymentMilestoneSerializer` defines:
  - `project_title = serializers.CharField(source='contract.bid.project.title')`
  - `freelancer_email = serializers.EmailField(source='contract.bid.freelancer.email')`
  `get_contract_milestones()` executes `PaymentMilestone.objects.filter(contract_id=contract_id)` with zero `select_related`.
- **PROBLEMATIC CODE:**
  ```python
  def get_contract_milestones(contract_id):
      """Get all milestones for a contract"""
      return PaymentMilestone.objects.filter(
          contract_id=contract_id
      ).order_by('due_date', 'created_at')
  ```
- **WHY IT CAUSES N+1:** For each milestone in a contract table, DRF queries `milestone.contract.bid.project` and `milestone.contract.bid.freelancer`, generating $2 \times N$ queries.
- **FIX:**
  ```python
  def get_contract_milestones(contract_id):
      """Get all milestones for a contract"""
      return PaymentMilestone.objects.filter(
          contract_id=contract_id
      ).select_related(
          'contract__bid__project',
          'contract__bid__freelancer'
      ).order_by('due_date', 'created_at')

  def get_upcoming_milestones(user, days=30, limit=10):
      ...
      return PaymentMilestone.objects.filter(
          contract_id__in=contract_ids,
          status=PaymentMilestone.Status.PENDING,
          due_date__lte=end_date
      ).select_related(
          'contract__bid__project',
          'contract__bid__freelancer'
      ).order_by('due_date')[:limit]
  ```

---

### Issue PAY-03: Reverse OneToOne Escrow Access in Payout Task
- **FILE:** `apps/payments/tasks.py`
- **FUNCTION:** `razorpay_transfer_to_freelancer_task()`
- **PROBLEM:** The task queries `Payment.objects.select_related("contract__bid__freelancer__freelancer_profile", "contract__bid__project").get(id=payment_id)`. Later on line 123, it executes `escrow = payment.escrow`.
- **PROBLEMATIC CODE:**
  ```python
  payment = Payment.objects.select_related(
      "contract__bid__freelancer__freelancer_profile",
      "contract__bid__project",
  ).get(id=payment_id)
  ...
  escrow = payment.escrow  # Triggers un-selected reverse OneToOne query
  ```
- **WHY IT CAUSES N+1:** In Django, reverse `OneToOneField` relations execute a separate SQL query when accessed if not explicitly included in `select_related`.
- **FIX:**
  ```python
  payment = Payment.objects.select_related(
      "escrow",
      "contract__bid__freelancer__freelancer_profile",
      "contract__bid__project",
  ).get(id=payment_id)
  ```

---

## 5. `apps/worklogs`

---

### Issue WRK-01: WorkLogViewSet Root Queryset Missing Full Eager Loading
- **FILE:** `apps/worklogs/views/views.py`
- **FUNCTION:** `WorkLogViewSet.get_queryset()`
- **PROBLEM:** When no `contract` query parameter is supplied, `WorkLogViewSet.get_queryset()` falls back to raw `WorkLog.objects.filter(...)` with zero `select_related`.
- **PROBLEMATIC CODE:**
  ```python
  def get_queryset(self):
      user = self.request.user
      contract_id = self.request.query_params.get('contract')
      
      if contract_id:
          queryset = get_contract_worklogs(contract_id)
          if user.role == 'FREELANCER':
              return queryset.filter(freelancer=user)
          return queryset.filter(contract__bid__project__client=user)
      
      if user.role == 'FREELANCER':
          return WorkLog.objects.filter(freelancer=user)
      
      return WorkLog.objects.filter(
          contract__bid__project__client=user
      )
  ```
- **WHY IT CAUSES N+1:** `WorkLogSerializer` serializes:
  1. `freelancer` (`UserSerializer` → `freelancer_profile`, `client_profile`)
  2. `contract` (`ContractSerializer` → `project`, `freelancer`, `client`, `bid`)
  Listing 50 worklogs produces over 300 individual SQL queries!
- **FIX:**
  ```python
  def get_queryset(self):
      user = self.request.user
      contract_id = self.request.query_params.get('contract')
      
      base_qs = WorkLog.objects.select_related(
          'freelancer',
          'freelancer__freelancer_profile',
          'freelancer__client_profile',
          'contract',
          'contract__bid__project',
          'contract__bid__project__client',
          'contract__bid__project__client__client_profile',
          'contract__bid__project__client__freelancer_profile',
          'contract__bid__freelancer',
          'contract__bid__freelancer__freelancer_profile',
          'contract__bid__freelancer__client_profile',
      ).prefetch_related('contract__bid__project__skills')
      
      if contract_id:
          base_qs = base_qs.filter(contract_id=contract_id)
      
      if user.role == 'FREELANCER':
          return base_qs.filter(freelancer=user)
      return base_qs.filter(contract__bid__project__client=user)
  ```

---

### Issue WRK-02: WorkLog Selectors Incomplete Relation Chains
- **FILE:** `apps/worklogs/selectors.py`
- **FUNCTION:** `get_contract_worklogs()`, `get_freelancer_worklogs()`, `get_contract_weekly_reports()`
- **PROBLEM:** `get_contract_worklogs` selects `'freelancer', 'contract__bid__project'`, but omits the full chain (`contract__bid__project__client`, `contract__bid__freelancer`, and user profile models) required by `ContractSerializer`.
- **PROBLEMATIC CODE:**
  ```python
  def get_contract_worklogs(contract_id: int, start_date=None, end_date=None):
      queryset = WorkLog.objects.filter(
          contract_id=contract_id
      ).select_related('freelancer', 'contract__bid__project')
      ...
  ```
- **WHY IT CAUSES N+1:** Every work log accesses unselected relations on the contract and participant models during serialization.
- **FIX:**
  ```python
  def get_contract_worklogs(contract_id: int, start_date=None, end_date=None):
      queryset = WorkLog.objects.filter(
          contract_id=contract_id
      ).select_related(
          'freelancer',
          'freelancer__freelancer_profile',
          'freelancer__client_profile',
          'contract__bid__project',
          'contract__bid__project__client',
          'contract__bid__freelancer',
      )
      if start_date:
          queryset = queryset.filter(date__gte=start_date)
      if end_date:
          queryset = queryset.filter(date__lte=end_date)
      return queryset
  ```

---

### Issue WRK-03: Deliverable Selectors Missing Reviewer & Contract Participants
- **FILE:** `apps/worklogs/selectors.py` & `apps/worklogs/views/views.py`
- **FUNCTION:** `get_freelancer_deliverables()`, `get_client_deliverables()`, `DeliverableViewSet.get_queryset()`
- **PROBLEM:** `DeliverableSerializer` serializes `freelancer`, `reviewed_by`, and `contract`. In `get_freelancer_deliverables()`, neither `freelancer` nor `reviewed_by` are in `select_related`.
- **PROBLEMATIC CODE:**
  ```python
  def get_freelancer_deliverables(freelancer, contract_id=None, status=None):
      queryset = Deliverable.objects.filter(freelancer=freelancer)
      if contract_id:
          queryset = queryset.filter(contract_id=contract_id)
      if status:
          queryset = queryset.filter(status=status)
      return queryset.select_related('contract__bid__project')
  ```
- **WHY IT CAUSES N+1:** `DeliverableSerializer` accesses `deliverable.freelancer` and `deliverable.reviewed_by` (each serialized with `UserSerializer`), triggering 4+ queries per deliverable.
- **FIX:**
  ```python
  def get_freelancer_deliverables(freelancer, contract_id=None, status=None):
      queryset = Deliverable.objects.filter(freelancer=freelancer)
      if contract_id:
          queryset = queryset.filter(contract_id=contract_id)
      if status:
          queryset = queryset.filter(status=status)
      return queryset.select_related(
          'freelancer',
          'freelancer__freelancer_profile',
          'freelancer__client_profile',
          'reviewed_by',
          'reviewed_by__freelancer_profile',
          'reviewed_by__client_profile',
          'contract__bid__project',
          'contract__bid__project__client',
          'contract__bid__freelancer',
      )
  ```

---

### Issue WRK-04: Periodic Celery Sweep N-Query Loop
- **FILE:** `apps/worklogs/tasks.py`
- **FUNCTION:** `generate_weekly_reports_for_all_contracts()`
- **PROBLEM:** The Celery Beat task iterates over every active contract and executes a separate `WorkLog.objects.filter(contract=contract, ...).exists()` query inside the loop.
- **PROBLEMATIC CODE:**
  ```python
  @shared_task(queue="freelanceflow_low_priority")
  def generate_weekly_reports_for_all_contracts():
      ...
      active_contracts = Contract.objects.filter(
          is_active=True,
      ).exclude(report_schedule__is_active=True)

      triggered = 0
      for contract in active_contracts:
          has_logs = WorkLog.objects.filter(
              contract=contract,
              date__range=[last_monday, last_monday + timedelta(days=6)],
          ).exists()

          if has_logs:
              generate_ai_report_task.delay(
                  contract.id,
                  last_monday.isoformat(),
                  7,
              )
              triggered += 1

      return {"triggered": triggered}
  ```
- **WHY IT CAUSES N+1:** For $N$ active contracts, $N$ separate SQL queries are executed against the database. If there are 1,000 active contracts, this executes 1,000 queries.
- **FIX:** Batch evaluate all active contracts that have logs using a single subquery or `values_list('contract_id', flat=True)`:
  ```python
  @shared_task(queue="freelanceflow_low_priority")
  def generate_weekly_reports_for_all_contracts():
      today = date.today()
      last_monday = today - timedelta(days=today.weekday() + 7)
      week_end = last_monday + timedelta(days=6)

      # 1 single query replaces N queries
      active_contract_ids = Contract.objects.filter(
          is_active=True,
      ).exclude(report_schedule__is_active=True).values_list('id', flat=True)

      contracts_with_logs = WorkLog.objects.filter(
          contract_id__in=active_contract_ids,
          date__range=[last_monday, week_end],
      ).values_list('contract_id', flat=True).distinct()

      triggered = 0
      for contract_id in contracts_with_logs:
          generate_ai_report_task.delay(
              contract_id,
              last_monday.isoformat(),
              7,
          )
          triggered += 1

      return {"triggered": triggered}
  ```

---

## 6. `apps/messaging`

---

### Issue MSG-01: SerializerMethodField Per-Item DB Hits & Missing Annotation
- **FILE:** `apps/messaging/serializers/serializers.py`
- **FUNCTION:** `ConversationSerializer.get_last_message()` and `ConversationSerializer.get_unread_count()`
- **PROBLEM:** `ConversationSerializer` defines two `SerializerMethodField` properties that execute database queries for every single conversation item in the list.
- **PROBLEMATIC CODE:**
  ```python
  class ConversationSerializer(serializers.ModelSerializer):
      contract = ContractSerializer(read_only=True)
      last_message = serializers.SerializerMethodField()
      unread_count = serializers.SerializerMethodField()
      
      def get_last_message(self, obj):
          last_msg = obj.messages.order_by('-created_at').first()
          if last_msg:
              return MessageSerializer(last_msg).data
          return None
      
      def get_unread_count(self, obj):
          user = self.context.get('request').user
          return obj.messages.filter(is_read=False).exclude(sender=user).count()
  ```
- **WHY IT CAUSES N+1:** For an inbox with 20 conversations:
  1. `get_last_message` runs 20 queries for `obj.messages.first()`, plus additional queries for `sender` and user profiles inside `MessageSerializer`.
  2. `get_unread_count` runs 20 queries for `COUNT(*)`.
  3. `contract` runs queries for `bid`, `project`, `client`, `freelancer`.
  Total queries for 20 conversations exceed **100+ SQL queries**.
- **FIX:**
  1. Annotate `unread_count` directly on the queryset using `Count()`.
  2. Prefetch the latest message and select all participants.
  ```python
  # apps/messaging/selectors.py
  from django.db.models import Count, Q, Prefetch

  def get_user_conversations(user) -> QuerySet[Conversation]:
      """Get all conversations for a user with pre-annotated unread count and prefetched relations."""
      return Conversation.objects.filter(
          Q(contract__bid__freelancer=user) | Q(contract__bid__project__client=user)
      ).select_related(
          'contract__bid__project__client',
          'contract__bid__project__client__client_profile',
          'contract__bid__project__client__freelancer_profile',
          'contract__bid__freelancer',
          'contract__bid__freelancer__freelancer_profile',
          'contract__bid__freelancer__client_profile',
      ).annotate(
          annotated_unread_count=Count(
              'messages',
              filter=Q(messages__is_read=False) & ~Q(messages__sender=user)
          )
      ).prefetch_related(
          Prefetch(
              'messages',
              queryset=Message.objects.select_related(
                  'sender',
                  'sender__freelancer_profile',
                  'sender__client_profile'
              ).order_by('-created_at'),
              to_attr='prefetched_messages'
          )
      )

  # apps/messaging/serializers/serializers.py
  class ConversationSerializer(serializers.ModelSerializer):
      contract = ContractSerializer(read_only=True)
      last_message = serializers.SerializerMethodField()
      unread_count = serializers.SerializerMethodField()

      def get_last_message(self, obj):
          # Read from prefetched list (in-memory, 0 DB queries)
          if hasattr(obj, 'prefetched_messages') and obj.prefetched_messages:
              return MessageSerializer(obj.prefetched_messages[0]).data
          last_msg = obj.messages.order_by('-created_at').first()
          return MessageSerializer(last_msg).data if last_msg else None

      def get_unread_count(self, obj):
          # Read from DB annotation (0 DB queries)
          if hasattr(obj, 'annotated_unread_count'):
              return obj.annotated_unread_count
          user = self.context.get('request').user
          return obj.messages.filter(is_read=False).exclude(sender=user).count()
  ```

---

### Issue MSG-02: Message Sender Profiles Missing in Message List
- **FILE:** `apps/messaging/selectors.py` & `apps/messaging/views/views.py`
- **FUNCTION:** `get_conversation_messages()` and `MessageViewSet.get_queryset()`
- **PROBLEM:** Queryset uses `.select_related('sender')`. `MessageSerializer` uses `sender = UserSerializer(read_only=True)`, which accesses `sender.freelancer_profile` and `sender.client_profile`.
- **PROBLEMATIC CODE:**
  ```python
  def get_conversation_messages(conversation_id: int, limit: int = 50) -> QuerySet[Message]:
      return Message.objects.filter(
          conversation_id=conversation_id
      ).select_related('sender').order_by('-created_at')[:limit]
  ```
- **WHY IT CAUSES N+1:** For 50 messages, DRF makes 100 extra queries to fetch profiles for each message sender.
- **FIX:**
  ```python
  def get_conversation_messages(conversation_id: int, limit: int = 50) -> QuerySet[Message]:
      return Message.objects.filter(
          conversation_id=conversation_id
      ).select_related(
          'sender',
          'sender__freelancer_profile',
          'sender__client_profile'
      ).order_by('-created_at')[:limit]
  ```

---

## 7. `apps/notifications`

---

### Issue NOT-01: Digest Email User Profile Traversal
- **FILE:** `apps/notifications/services/services_digest.py`
- **FUNCTION:** `get_pending_digests()`
- **PROBLEM:** `get_pending_digests()` returns `DigestEmail.objects.filter(is_enabled=True, next_send_at__lte=timezone.now())` without `.select_related('user')`.
- **PROBLEMATIC CODE:**
  ```python
  def get_pending_digests():
      """Get digests that need to be sent"""
      from django.utils import timezone
      return DigestEmail.objects.filter(
          is_enabled=True,
          next_send_at__lte=timezone.now()
      )
  ```
- **WHY IT CAUSES N+1:** When iterating over pending digests to construct and dispatch emails, accessing `digest.user.email` triggers a separate query for each digest subscription.
- **FIX:**
  ```python
  def get_pending_digests():
      """Get digests that need to be sent"""
      from django.utils import timezone
      return DigestEmail.objects.filter(
          is_enabled=True,
          next_send_at__lte=timezone.now()
      ).select_related('user')
  ```

---

## 8. `apps/search`

---

### Issue SCH-01: Bulk Elasticsearch Index Rebuild N+1 Queries
- **FILE:** `apps/search/documents.py`
- **FUNCTION:** `ProjectDocument.Django` and `FreelancerDocument.Django`
- **PROBLEM:** `ProjectDocument` extracts `client_name = fields.TextField(attr="client.get_full_name")`, `client_email = fields.KeywordField(attr="client.email")`, and `prepare_skills` iterates over `instance.skills.all()`. Neither `ProjectDocument.Django` nor `FreelancerDocument.Django` overrides `get_queryset()`.
- **PROBLEMATIC CODE:**
  ```python
  @registry.register_document
  class ProjectDocument(Document):
      client_name = fields.TextField(attr="client.get_full_name")
      client_email = fields.KeywordField(attr="client.email")
      skills = fields.KeywordField(multi=True)
      ...
      class Django:
          model = Project
          fields = [...]
          # Missing get_queryset() override
  ```
- **WHY IT CAUSES N+1:** Running `python manage.py search_index --rebuild` performs a full table scan. For 10,000 projects, it executes 10,000 queries for `project.client` and 10,000 queries for `project.skills.all()` (20,000+ unnecessary queries).
- **FIX:** Override `get_queryset()` in the `Django` inner class of both documents:
  ```python
  @registry.register_document
  class ProjectDocument(Document):
      ...
      class Django:
          model = Project
          fields = [
              "id",
              "title",
              "description",
              "budget",
              "deadline",
              "created_at",
              "updated_at",
          ]
          related_models = [User]

          def get_queryset(self):
              return super().get_queryset().select_related('client').prefetch_related('skills')


  @registry.register_document
  class FreelancerDocument(Document):
      ...
      class Django:
          model = FreelancerProfile
          fields = [
              "id",
              "bio",
              "hourly_rate",
              "subscription_tier",
              "total_earned",
              "created_at",
          ]
          related_models = [User]

          def get_queryset(self):
              return super().get_queryset().select_related('user')
  ```

---

## 9. Architecture Best Practices & Summary Matrix

### Quick Reference Problem & Fix Matrix

| App | Identifier | Layer | Problem Summary | Required ORM Optimization |
|---|---|---|---|---|
| `users` | USR-01 | View | `UserSerializer` reverse OneToOne profiles | `.select_related('freelancer_profile', 'client_profile')` |
| `users` | USR-02 | Service | Activity log `user.email` traversal | `.select_related('user')` |
| `projects` | PRJ-01 | Selector | `client` user profiles in project serializers | `.select_related('client__client_profile', 'client__freelancer_profile')` |
| `projects` | PRJ-02 | Service | Bookmark `project.client.email` traversal | `.select_related('project__client')` |
| `projects` | PRJ-03 | View | Project bids action nested client profiles | `.select_related('project__client__client_profile', 'project__client__freelancer_profile')` |
| `bidding` | BID-01 | View | Client bid list missing client & freelancer profiles | Add multi-hop `select_related` and `prefetch_related('project__skills')` |
| `bidding` | BID-02 | Selector | Active contracts missing nested project & client data | Add full `bid__project__client` and `bid__freelancer` chains |
| `bidding` | BID-03 | Service/View | Review serializer traversing both reviewer and reviewee | Add `reviewer__*` and `reviewee__*` profile chains |
| `bidding` | BID-04 | Service | Retraction detail accessing `retraction.bid.project.title` | `.select_related('bid__project')` |
| `payments` | PAY-01 | Selector | Payment history accessing freelancer and client names | `.select_related('contract__bid__project__client', 'contract__bid__freelancer')` |
| `payments` | PAY-02 | Service | Milestone serializer traversing contract, project, and freelancer | `.select_related('contract__bid__project', 'contract__bid__freelancer')` |
| `payments` | PAY-03 | Task | Celery payout task accessing reverse OneToOne `payment.escrow` | Add `"escrow"` to `Payment.objects.select_related()` |
| `worklogs` | WRK-01 | View | `WorkLogViewSet.get_queryset()` fallback missing eager loading | Full `freelancer` and `contract` multi-hop `select_related` |
| `worklogs` | WRK-02 | Selector | Worklog selectors missing nested contract participants | Add complete participant graph to `select_related` |
| `worklogs` | WRK-03 | Selector/View | Deliverable selectors missing reviewer and client relations | Add `freelancer__*`, `reviewed_by__*`, and `contract__bid__*` |
| `worklogs` | WRK-04 | Task | Weekly report Celery task querying `exists()` in loop | Batch with `values_list('contract_id', flat=True).distinct()` |
| `messaging` | MSG-01 | Serializer | `get_last_message` & `get_unread_count` DB hits per conversation | Annotate `Count()` and `Prefetch('messages')` |
| `messaging` | MSG-02 | Selector | Message list missing sender profiles | `.select_related('sender__freelancer_profile', 'sender__client_profile')` |
| `notifications`| NOT-01 | Service | Pending digests missing user FK | `.select_related('user')` |
| `search` | SCH-01 | Document | Bulk indexing doing per-row FK and M2M queries | Add `get_queryset()` with `select_related` and `prefetch_related` |

---

### Core Architectural Rules for FreelanceFlow Monolith

1. **Rule of Reverse OneToOne Relationships:**
   Because Django models `FreelancerProfile` and `ClientProfile` have `OneToOneField(User, related_name='...')`, serializing `User` with `UserSerializer` triggers a query for each profile unless explicitly prefetched with `select_related('freelancer_profile', 'client_profile')`.

2. **Rule of SerializerMethodField:**
   Never execute `.count()`, `.exists()`, `.first()`, or `.filter()` inside a `SerializerMethodField` for list endpoints. Always compute them in the selector layer using SQL annotations (`annotate(unread_count=Count(...))`) or in-memory prefetches (`Prefetch(..., to_attr=...)`).

3. **Rule of Celery Batching:**
   Never loop over a parent queryset and run child `.filter().exists()` checks. Use reverse filtering or `values_list()` to let the database engine perform the set intersection in a single query.
