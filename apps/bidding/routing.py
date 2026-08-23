from django.urls import re_path
from .consumers import ProjectConsumer, ContractDraftConsumer

websocket_urlpatterns = [
    re_path(r'^ws/project/(?P<project_id>\d+)/$', ProjectConsumer.as_asgi()),
    re_path(r'^ws/contract-draft/(?P<contract_id>\d+)/$', ContractDraftConsumer.as_asgi()),
]
