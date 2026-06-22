from django.urls import path, include
from .urls import urlpatterns as core_urls
from .urls_extended import urlpatterns as extended_urls

urlpatterns = [
    path('', include(core_urls)),
    path('', include(extended_urls)),
]
