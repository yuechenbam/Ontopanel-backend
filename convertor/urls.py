from django.urls import path
from django.urls import path
from . import views

urlpatterns = [
    path("", views.GraphConvertor.as_view(), name="graph_convertor")
]
