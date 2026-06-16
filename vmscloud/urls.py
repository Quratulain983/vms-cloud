from django.contrib import admin
from django.urls import path, include
from vms.views import health_check 


urlpatterns = [
    path("admin/", admin.site.urls),
    path('vms/api/v1/', include('vms.urls', namespace='vms')),
    path("health/", health_check),
]