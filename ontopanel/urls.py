"""ontopanel URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Ontopanel API",
        default_version="v1",
        description='''
        Ontopanel is a diagrams.net plugin that assists graphically ontology devleopment in diagrams.net.\n
        Github backend source: https: // github.com/yuechenbam/Ontopanel-backend.\n
        This API works with Ontopanel-frontend(https: // github.com/yuechenbam/Ontopanel-frontend).''',
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="yue.chen@bam.de"),
        license=openapi.License(name="Apache-2.0 license"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("api/v1/", include("owl_processor.urls"), name='owl_processor'),
    path("api/v1/user/", include("user.urls"), name='user'),
    path("api/v1/convertor/", include("convertor.urls"), name='convertor'),
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger',
         cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc',
         cache_timeout=0), name='schema-redoc'),
]
