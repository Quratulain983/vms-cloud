from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('vms/api/v1/', include('vms.urls', namespace='vms')),
]