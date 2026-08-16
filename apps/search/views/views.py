from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response

from elasticsearch_dsl import Q
from apps.search.documents import ProjectDocument, FreelancerDocument
from apps.search.serializers import (
    SearchQuerySerializer,
    ProjectSearchSerializer,
    FreelancerSearchSerializer
)
from core.pagination import StandardResultsPagination
class SearchView(APIView):
    """
    Unified search endpoint for projects and freelancers.
    
    GET /api/search/?q=web+developer&type=projects&skills=python,django
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsPagination
    
    def get(self, request):
        """Handle search requests."""
        serializer = SearchQuerySerializer(data=request.query_params)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query_data = serializer.validated_data
        search_query = query_data.get("q", "")
        search_type = query_data.get("type", "all")
        skills = query_data.get("skills", "")
        min_budget = query_data.get("min_budget")
        max_budget = query_data.get("max_budget")
        
        results = {
            "projects": [],
            "freelancers": []
        }
        
        # Search projects
        if search_type in ["projects", "all"]:
            project_results = self._search_projects(
                search_query, skills, min_budget, max_budget
            )
            results["projects"] = ProjectSearchSerializer(
                project_results, many=True
            ).data
        
        # Search freelancers
        if search_type in ["freelancers", "all"]:
            freelancer_results = self._search_freelancers(search_query, skills)
            results["freelancers"] = FreelancerSearchSerializer(
                freelancer_results, many=True
            ).data
        
        return Response(results)
    
    def _search_projects(self, query, skills, min_budget, max_budget):
        """Search projects using Elasticsearch with PostgreSQL DB fallback."""
        try:
            search = ProjectDocument.search()
            if query:
                search = search.query(
                    Q("multi_match", query=query, fields=["title^3", "description", "skills"])
                )
            if skills:
                skill_list = [s.strip() for s in skills.split(",")]
                search = search.filter("terms", skills=skill_list)
            if min_budget is not None:
                search = search.filter("range", budget={"gte": float(min_budget)})
            if max_budget is not None:
                search = search.filter("range", budget={"lte": float(max_budget)})

            search = search.filter("term", status="OPEN")
            response = search[:50].execute()
            return [hit.to_dict() for hit in response]
        except Exception:
            from apps.projects.models import Project
            qs = Project.objects.filter(status="OPEN")
            if query:
                qs = qs.filter(title__icontains=query)
            return [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "status": p.status,
                    "budget": float(p.budget_max or p.budget_min or 0),
                    "client_id": p.client_id,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in qs[:50]
            ]

    def _search_freelancers(self, query, skills):
        """Search freelancers using Elasticsearch with PostgreSQL DB fallback."""
        try:
            search = FreelancerDocument.search()
            if query:
                search = search.query(
                    Q("multi_match", query=query, fields=["full_name^2", "bio", "skills"])
                )
            if skills:
                skill_list = [s.strip() for s in skills.split(",")]
                search = search.filter("terms", skills=skill_list)

            response = search[:50].execute()
            return [hit.to_dict() for hit in response]
        except Exception:
            from apps.users.models import FreelancerProfile
            qs = FreelancerProfile.objects.select_related("user").all()
            if query:
                qs = qs.filter(title__icontains=query)
            return [
                {
                    "id": f.id,
                    "user_id": f.user_id,
                    "full_name": f.user.get_full_name() or f.user.email,
                    "title": f.title,
                    "bio": f.bio,
                    "hourly_rate": float(f.hourly_rate or 0),
                    "skills": f.skills if isinstance(f.skills, list) else [],
                }
                for f in qs[:50]
            ]


class ProjectSearchView(APIView):
    """Dedicated endpoint for project search with DB fallback."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        """Search projects."""
        query = request.query_params.get("q", "")
        skills = request.query_params.get("skills", "")

        try:
            search = ProjectDocument.search()
            if query:
                search = search.query(
                    Q("multi_match", query=query, fields=["title^3", "description"])
                )
            if skills:
                skill_list = [s.strip() for s in skills.split(",")]
                search = search.filter("terms", skills=skill_list)

            search = search.filter("term", status="OPEN")
            response = search[:50].execute()
            results = [hit.to_dict() for hit in response]
            return Response({"results": ProjectSearchSerializer(results, many=True).data})
        except Exception:
            from apps.projects.models import Project
            qs = Project.objects.filter(status="OPEN")
            if query:
                qs = qs.filter(title__icontains=query)
            results = [
                {
                    "id": p.id,
                    "title": p.title,
                    "description": p.description,
                    "status": p.status,
                    "budget": float(p.budget_max or p.budget_min or 0),
                    "client_id": p.client_id,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                }
                for p in qs[:50]
            ]
            return Response({"results": results})


class FreelancerSearchView(APIView):
    """Dedicated endpoint for freelancer search with DB fallback."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        """Search freelancers."""
        query = request.query_params.get("q", "")
        skills = request.query_params.get("skills", "")

        try:
            search = FreelancerDocument.search()
            if query:
                search = search.query(
                    Q("multi_match", query=query, fields=["full_name^2", "bio", "skills"])
                )
            if skills:
                skill_list = [s.strip() for s in skills.split(",")]
                search = search.filter("terms", skills=skill_list)

            response = search[:50].execute()
            results = [hit.to_dict() for hit in response]
            return Response({"results": FreelancerSearchSerializer(results, many=True).data})
        except Exception:
            from apps.users.models import FreelancerProfile
            qs = FreelancerProfile.objects.select_related("user").all()
            if query:
                qs = qs.filter(title__icontains=query)
            results = [
                {
                    "id": f.id,
                    "user_id": f.user_id,
                    "full_name": f.user.get_full_name() or f.user.email,
                    "title": f.title,
                    "bio": f.bio,
                    "hourly_rate": float(f.hourly_rate or 0),
                    "skills": f.skills if isinstance(f.skills, list) else [],
                }
                for f in qs[:50]
            ]
            return Response({"results": results})



class AutocompleteView(APIView):
    """
    Autocomplete suggestions endpoint.

    GET /api/search/autocomplete/?q=<query>
    Returns a list of search suggestions based on the query.
    Falls back gracefully when Elasticsearch is unavailable.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if not query:
            return Response({"suggestions": []}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from apps.search.services import get_autocomplete_suggestions
            suggestions = get_autocomplete_suggestions(query)
            return Response({"suggestions": suggestions})
        except Exception:
            # ES unavailable in local dev — return empty suggestions
            return Response({"suggestions": []})
