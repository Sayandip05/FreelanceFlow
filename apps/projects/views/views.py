from django.db.models import Q
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.projects.models import Project
from apps.projects.serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
)
from apps.projects.services import (
    create_project,
    update_project,
    close_project,
    delete_project,
)
from apps.projects.selectors import (
    get_project_by_id,
    get_open_projects,
    get_client_projects,
)
from apps.projects.permissions import IsProjectOwner
from apps.users.permissions import IsClient
from apps.bidding.serializers import BidListSerializer
from core.exceptions import ValidationError, PermissionDeniedError
class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Project CRUD operations.
    
    Endpoints:
    - GET /api/projects/ - List projects
    - POST /api/projects/ - Create project (clients only)
    - GET /api/projects/{id}/ - Get project detail
    - PATCH /api/projects/{id}/ - Update project (owner only)
    - DELETE /api/projects/{id}/ - Close project (owner only)
    """
    
    def get_queryset(self):
        """Get queryset based on user role and query params."""
        user = self.request.user
        
        # If client, return their projects
        if user.is_authenticated and getattr(user, 'role', None) == 'CLIENT':
            return get_client_projects(user)
        
        # For freelancers and public visitors, return open projects with filtering
        budget_min = self.request.query_params.get('budget_min')
        budget_max = self.request.query_params.get('budget_max')
        skills = self.request.query_params.getlist('skills')
        search = self.request.query_params.get('search')
        
        return get_open_projects(
            budget_min=float(budget_min) if budget_min else None,
            budget_max=float(budget_max) if budget_max else None,
            skills=skills if skills else None,
            search=search,
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ProjectUpdateSerializer
        elif self.action == 'list':
            return ProjectListSerializer
        return ProjectDetailSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsClient()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsProjectOwner()]
        elif self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            project = create_project(
                client=request.user,
                title=serializer.validated_data['title'],
                description=serializer.validated_data['description'],
                budget=serializer.validated_data['budget'],
                approx_duration=serializer.validated_data['approx_duration'],
                deadline=serializer.validated_data.get('deadline'),
                skills=serializer.validated_data.get('skill_names', []),
            )
            
            return Response(
                ProjectDetailSerializer(project).data,
                status=status.HTTP_201_CREATED,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        project = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        try:
            updated_project = update_project(
                project=project,
                user=request.user,
                title=serializer.validated_data.get('title'),
                description=serializer.validated_data.get('description'),
                budget=serializer.validated_data.get('budget'),
                approx_duration=serializer.validated_data.get('approx_duration'),
                deadline=serializer.validated_data.get('deadline'),
                skills=serializer.validated_data.get('skill_names'),
            )
            
            return Response(
                ProjectDetailSerializer(updated_project).data,
                status=status.HTTP_200_OK,
            )
        except ValidationError as e:
            return Response(
                {"error": e.message, "code": e.code, "field": e.field},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    def destroy(self, request, *args, **kwargs):
        project = self.get_object()
        
        try:
            delete_project(project, request.user)
            return Response(
                {"message": "Project deleted successfully."},
                status=status.HTTP_200_OK,
            )
        except (ValidationError, PermissionDeniedError) as e:
            return Response(
                {"error": getattr(e, "message", str(e)), "code": getattr(e, "code", "error"), "field": getattr(e, "field", None)},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    @action(detail=False, methods=['get'])
    def my_projects(self, request):
        """Get current user's projects (for clients)."""
        if request.user.role != 'CLIENT':
            return Response(
                {"error": "Only clients have projects.", "code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        projects = get_client_projects(request.user)
        serializer = ProjectListSerializer(projects, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def bids(self, request, pk=None):
        """Get all bids for a specific project."""
        project = self.get_object()
        
        # Only the client who created the project can view its bids
        if request.user.role != 'CLIENT' or project.client != request.user:
            return Response(
                {"error": "You do not have permission to view bids for this project.", "code": "permission_denied"},
                status=status.HTTP_403_FORBIDDEN,
            )
            
        bids = project.bids.all().select_related(
            'freelancer', 
            'freelancer__freelancer_profile', 
            'freelancer__client_profile', 
            'project', 
            'project__client',
            'project__client__client_profile',
            'project__client__freelancer_profile',
        ).prefetch_related('project__skills')
        
        page = self.paginate_queryset(bids)
        if page is not None:
            serializer = BidListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
            
        serializer = BidListSerializer(bids, many=True, context={"request": request})
        return Response(serializer.data)
