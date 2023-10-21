from django.conf import settings
from django.urls import path

from .views import components, check_hotreload

app_name = 'fryhcs'

urlpatterns = [
    path('components', components, name="components"),
]

if settings.DEBUG:
    urlpatterns += [
        path('_hotreload', hotreload, name="hotreload"),
    ]
