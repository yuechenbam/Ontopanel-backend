"""ontopanel URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("api/v1/", include("owl_processor.urls"), name='owl_processor'),
    path("api/v1/user/", include("user.urls"), name='user'),
    path("api/v1/convertor/", include("convertor.urls"), name='convertor'),
    path('admin/', admin.site.urls),
]
