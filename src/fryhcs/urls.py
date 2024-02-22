from django.conf import settings
from django.urls import path

from .views import component, check_hotreload

app_name = 'fryhcs'

urlpatterns = [
#    path('component', components, name="component"),
]

if settings.DEBUG:
    urlpatterns += [
        path('_check_hotreload', check_hotreload, name="check_hotreload"),
    ]
