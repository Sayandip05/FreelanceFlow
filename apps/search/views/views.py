from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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
    permission_classes = [IsAuthenticated]
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
        """Search projects using Elasticsearch."""
        search = ProjectDocument.search()
        
        # Text search
        if query:
            search = search.query(
                Q("multi_match", query=query, fields=["title^3", "description", "skills"])
            )
        
        # Filter by skills
        if skills:
            skill_list = [s.strip() for s in skills.split(",")]
            search = search.filter("terms", skills=skill_list)
        
        # Filter by budget range
        if min_budget is not None:
            search = search.filter("range", budget={"gte": float(min_budget)})
        if max_budget is not None:
            search = search.filter("range", budget={"lte": float(max_budget)})
        
        # Only show open projects
        search = search.filter("term", status="OPEN")
        
        # Execute and return results
        response = search[:50].execute()
        return [hit.to_dict() for hit in response]
    
    def _search_freelancers(self, query, skills):
        """Search freelancers using Elasticsearch."""
        search = FreelancerDocument.search()
        
        # Text search
        if query:
            search = search.query(
                Q("multi_match", query=query, fields=["full_name^2", "bio", "skills"])
            )
        
        # Filter by skills
        if skills:
            skill_list = [s.strip() for s in skills.split(",")]
            search = search.filter("terms", skills=skill_list)
        
        # All indexed freelancers are considered available
        pass  # No availability filter needed
        
        # Execute and return results
        response = search[:50].execute()
        return [hit.to_dict() for hit in response]


class ProjectSearchView(APIView):
    """Dedicated endpoint for project search."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search projects."""
        query = request.query_params.get("q", "")
        skills = request.query_params.get("skills", "")
        
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


class FreelancerSearchView(APIView):
    """Dedicated endpoint for freelancer search."""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search freelancers."""
        query = request.query_params.get("q", "")
        skills = request.query_params.get("skills", "")
        
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
