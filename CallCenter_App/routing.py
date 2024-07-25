from django.urls import re_path
from .consumers import UserBreakConsumer, AllBreaksConsumer

websocket_urlpatterns = [
    re_path(r'ws/break-monitor/(?P<user_id>\d+)/$', UserBreakConsumer.as_asgi()),
    re_path(r'ws/break-monitor/all/$', AllBreaksConsumer.as_asgi()),

]





