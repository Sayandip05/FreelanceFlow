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
            try:
                project_results = self._search_projects(
                    search_query, skills, min_budget, max_budget
                )
                results["projects"] = ProjectSearchSerializer(
                    project_results, many=True
                ).data
            except Exception:
                # Fallback to database
                from apps.projects.models import Project
                from django.db.models import Q as DB_Q
                qs = Project.objects.filter(status="OPEN")
                if search_query:
                    qs = qs.filter(
                        DB_Q(title__icontains=search_query) |
                        DB_Q(description__icontains=search_query)
                    )
                if skills:
                    skill_list = [s.strip().lower() for s in skills.split(",")]
                    for skill in skill_list:
                        qs = qs.filter(skills__skill_name__icontains=skill)
                if min_budget is not None:
                    qs = qs.filter(budget__gte=float(min_budget))
                if max_budget is not None:
                    qs = qs.filter(budget__lte=float(max_budget))
                results["projects"] = [{
                    "id": p.id,
                    "title": p.title,
                    "short_description": p.short_description,
                    "description": p.description,
                    "budget": str(p.budget),
                    "status": p.status,
                    "client": {
                        "id": p.client.id,
                        "email": p.client.email,
                        "first_name": p.client.first_name,
                        "last_name": p.client.last_name,
                        "full_name": p.client.full_name,
                    }
                } for p in qs[:50]]
        
        # Search freelancers
        if search_type in ["freelancers", "all"]:
            try:
                freelancer_results = self._search_freelancers(search_query, skills)
                results["freelancers"] = FreelancerSearchSerializer(
                    freelancer_results, many=True
                ).data
            except Exception:
                # Fallback to database with review-based ranking
                from apps.users.models import User
                from django.db.models import Q as DB_Q
                qs = User.objects.filter(role="FREELANCER", freelancer_profile__is_onboarded=True)
                if search_query:
                    qs = qs.filter(
                        DB_Q(first_name__icontains=search_query) |
                        DB_Q(last_name__icontains=search_query) |
                        DB_Q(freelancer_profile__bio__icontains=search_query)
                    )
                if skills:
                    skill_list = [s.strip().lower() for s in skills.split(",")]
                    matching_user_ids = []
                    for u in qs:
                        user_skills = [s.lower() for s in (u.freelancer_profile.skills if u.freelancer_profile else [])]
                        if any(skill in user_skills for skill in skill_list):
                            matching_user_ids.append(u.id)
                    qs = User.objects.filter(id__in=matching_user_ids)
                
                # Review-based ranking: highest rated first, then total reviews, then total earned
                qs = qs.order_by(
                    "-freelancer_profile__average_rating",
                    "-freelancer_profile__total_reviews",
                    "-freelancer_profile__total_earned",
                    "-id"
                )
                results["freelancers"] = [{
                    "id": u.id,
                    "user_id": u.id,
                    "email": u.email,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "full_name": u.full_name,
                    "role": u.role,
                    "freelancer_profile": {
                        "bio": u.freelancer_profile.bio if u.freelancer_profile else "",
                        "skills": u.freelancer_profile.skills if u.freelancer_profile else [],
                        "hourly_rate": str(u.freelancer_profile.hourly_rate) if u.freelancer_profile and u.freelancer_profile.hourly_rate else "0.00",
                        "city": u.freelancer_profile.city if u.freelancer_profile else "",
                        "country": u.freelancer_profile.country if u.freelancer_profile else "",
                        "avatar": u.freelancer_profile.avatar if u.freelancer_profile and u.freelancer_profile.avatar else "",
                        "banner_image": u.freelancer_profile.banner_image if u.freelancer_profile and u.freelancer_profile.banner_image else "",
                        "experience_level": u.freelancer_profile.experience_level if u.freelancer_profile else "Intermediate",
                        "average_rating": float(u.freelancer_profile.average_rating) if u.freelancer_profile and u.freelancer_profile.average_rating else 0.0,
                        "total_reviews": u.freelancer_profile.total_reviews if u.freelancer_profile else 0,
                        "is_onboarded": u.freelancer_profile.is_onboarded if u.freelancer_profile else True,
                    }
                } for u in qs[:50]]
        
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
        """Search freelancers using Elasticsearch ranked primarily by ratings and reviews."""
        try:
            search = FreelancerDocument.search()
            if query:
                search = search.query(
                    Q("multi_match", query=query, fields=["full_name^2", "bio", "skills"])
                )
            if skills:
                skill_list = [s.strip().lower() for s in skills.split(",")]
                search = search.filter("terms", skills=skill_list)

            # Review & rating based ranking
            search = search.sort(
                {"average_rating": {"order": "desc"}},
                {"total_reviews": {"order": "desc"}},
                {"total_earned": {"order": "desc"}},
            )

            response = search[:50].execute()
            return [hit.to_dict() for hit in response]
        except Exception:
            from apps.users.models import FreelancerProfile
            qs = FreelancerProfile.objects.select_related("user").filter(is_onboarded=True).order_by(
                "-average_rating",
                "-total_reviews",
                "-total_earned",
                "-id"
            )
            if query:
                qs = qs.filter(title__icontains=query)
            return [
                {
                    "id": f.id,
                    "user_id": f.user_id,
                    "full_name": f.user.get_full_name() or f.user.email,
                    "first_name": f.user.first_name,
                    "last_name": f.user.last_name,
                    "email": f.user.email,
                    "avatar": f.avatar,
                    "banner_image": f.banner_image,
                    "city": f.city,
                    "country": f.country,
                    "experience_level": f.experience_level,
                    "average_rating": float(f.average_rating or 0),
                    "total_reviews": f.total_reviews,
                    "is_onboarded": f.is_onboarded,
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
        search = ProjectDocument.search()
        
        if query:
            search = search.query(
                Q("multi_match", query=query, fields=["title^3", "description"])
            )
        
        if skills:
            skill_list = [s.strip() for s in skills.split(",")]
            search = search.filter("terms", skills=skill_list)
        
        search = search.filter("term", status="OPEN")
        
        try:
            response = search[:50].execute()
            results = [hit.to_dict() for hit in response]
            data = ProjectSearchSerializer(results, many=True).data
        except Exception:
            # Fallback to database
            from apps.projects.models import Project
            from django.db.models import Q as DB_Q
            qs = Project.objects.filter(status="OPEN")
            if query:
                qs = qs.filter(
                    DB_Q(title__icontains=query) |
                    DB_Q(description__icontains=query)
                )
            if skills:
                skill_list = [s.strip().lower() for s in skills.split(",")]
                for skill in skill_list:
                    qs = qs.filter(skills__skill_name__icontains=skill)
            results = []
            for p in qs[:50]:
                results.append({
                    "id": p.id,
                    "title": p.title,
                    "short_description": p.short_description,
                    "description": p.description,
                    "budget": str(p.budget),
                    "status": p.status,
                    "client": {
                        "id": p.client.id,
                        "email": p.client.email,
                        "first_name": p.client.first_name,
                        "last_name": p.client.last_name,
                        "full_name": p.client.full_name,
                    }
                })
            data = results
        
        return Response({"results": data})


class FreelancerSearchView(APIView):
    """Dedicated endpoint for freelancer search with review-based recommendation ranking."""
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self, request):
        """Search and rank freelancers primarily by reviews and ratings."""
        query = request.query_params.get("q", "")
        skills = request.query_params.get("skills", "")
        search = FreelancerDocument.search()
        
        if query:
            search = search.query(
                Q("multi_match", query=query, fields=["full_name^2", "bio", "skills"])
            )
        
        if skills:
            skill_list = [s.strip().lower() for s in skills.split(",")]
            search = search.filter("terms", skills=skill_list)
        
        # Rank by review rating (highest first), then total reviews, then total earned
        search = search.sort(
            {"average_rating": {"order": "desc"}},
            {"total_reviews": {"order": "desc"}},
            {"total_earned": {"order": "desc"}},
        )
        
        try:
            response = search[:50].execute()
            results = [hit.to_dict() for hit in response]
            data = FreelancerSearchSerializer(results, many=True).data
        except Exception:
            # Fallback to database with review-based ranking
            from apps.users.models import User
            from django.db.models import Q as DB_Q
            qs = User.objects.filter(role="FREELANCER", freelancer_profile__is_onboarded=True)
            if query:
                qs = qs.filter(
                    DB_Q(first_name__icontains=query) |
                    DB_Q(last_name__icontains=query) |
                    DB_Q(freelancer_profile__bio__icontains=query)
                )
            if skills:
                skill_list = [s.strip().lower() for s in skills.split(",")]
                matching_user_ids = []
                for u in qs:
                    user_skills = [s.lower() for s in (u.freelancer_profile.skills if u.freelancer_profile else [])]
                    if any(skill in user_skills for skill in skill_list):
                        matching_user_ids.append(u.id)
                qs = User.objects.filter(id__in=matching_user_ids)
            
            # Review-based ranking: highest rated first, then total reviews, then total earned
            qs = qs.order_by(
                "-freelancer_profile__average_rating",
                "-freelancer_profile__total_reviews",
                "-freelancer_profile__total_earned",
                "-id"
            )
            results = []
            for u in qs[:50]:
                fp = getattr(u, 'freelancer_profile', None)
                results.append({
                    "id": u.id,
                    "user_id": u.id,
                    "email": u.email,
                    "first_name": u.first_name,
                    "last_name": u.last_name,
                    "full_name": u.full_name,
                    "role": u.role,
                    "freelancer_profile": {
                        "bio": fp.bio if fp else "",
                        "skills": fp.skills if fp else [],
                        "hourly_rate": str(fp.hourly_rate) if fp and fp.hourly_rate else "0.00",
                        "city": fp.city if fp else "",
                        "country": fp.country if fp else "",
                        "avatar": fp.avatar if fp and fp.avatar else "",
                        "banner_image": fp.banner_image if fp and fp.banner_image else "",
                        "experience_level": fp.experience_level if fp else "Intermediate",
                        "average_rating": float(fp.average_rating) if fp and fp.average_rating else 0.0,
                        "total_reviews": fp.total_reviews if fp else 0,
                        "is_onboarded": fp.is_onboarded if fp else True,
                    }
                })
            data = results
        
        return Response({"results": data})


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
