from django.urls import re_path
from .consumers import ContractConsumer

websocket_urlpatterns = [
    re_path(r'^ws/contract/(?P<contract_id>\d+)/$', ContractConsumer.as_asgi()),
]
