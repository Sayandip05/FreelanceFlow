"""
Views for Extended Project Features
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from .serializers_extended import ProjectBookmarkSerializer, BookmarkProjectSerializer
from .services_bookmark import (
    bookmark_project, remove_bookmark, get_bookmarked_projects, is_bookmarked
)


class ProjectBookmarkViewSet(viewsets.ViewSet):
    """
    ViewSet for Project Bookmarks
    
    Endpoints:
    - POST /api/projects/{id}/bookmark/ - Bookmark a project
    - DELETE /api/projects/{id}/bookmark/ - Remove bookmark
    - GET /api/projects/bookmarks/ - Get bookmarked projects
    - GET /api/projects/{id}/is-bookmarked/ - Check if bookmarked
    """
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['post'])
    def bookmark(self, request, pk=None):
        """Bookmark a project"""
        from .models import Project
        
        try:
            project = Project.objects.get(id=pk)
            bookmark = bookmark_project(request.user, project)
            
            return Response({
                'message': 'Project bookmarked successfully',
                'bookmark': ProjectBookmarkSerializer(bookmark).data
            }, status=status.HTTP_201_CREATED)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['delete'])
    def bookmark(self, request, pk=None):
        """Remove bookmark from a project"""
        from .models import Project
        
        try:
            project = Project.objects.get(id=pk)
            remove_bookmark(request.user, project)
            
            return Response({
                'message': 'Bookmark removed successfully'
            }, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def list(self, request):
        """Get all bookmarked projects for current user"""
        bookmarks = get_bookmarked_projects(request.user)
        serializer = ProjectBookmarkSerializer(bookmarks, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='is-bookmarked')
    def is_bookmarked(self, request, pk=None):
        """Check if project is bookmarked"""
        from .models import Project
        
        try:
            project = Project.objects.get(id=pk)
            bookmarked = is_bookmarked(request.user, project)
            
            return Response({
                'is_bookmarked': bookmarked
            })
        except Project.DoesNotExist:
            return Response(
                {'error': 'Project not found'},
                status=status.HTTP_404_NOT_FOUND
            )
