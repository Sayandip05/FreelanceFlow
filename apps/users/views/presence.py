from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from apps.users.models import User

class UserPresenceView(APIView):
    """
    Returns the online presence status of a user based on their active WebSocket connections.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, *args, **kwargs):
        user = get_object_or_404(User, pk=pk)
        presence_key = f"presence_count_user_{user.id}"
        count = cache.get(presence_key, 0)
        
        return Response({
            "id": user.id,
            "is_online": count > 0,
        })
