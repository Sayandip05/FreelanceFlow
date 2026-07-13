from .urls import urlpatterns as base_urls
from .urls_extended import urlpatterns as extended_urls
urlpatterns = base_urls + extended_urls
