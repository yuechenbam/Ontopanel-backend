from django.urls import path
from django.urls import path
from . import views

urlpatterns = [
    path("ontos/lists/", views.OntoList.as_view(), name="onto_lists"),
    path("ontos/change/<int:id>", views.OntoChange.as_view(), name="onto_change"),
    path("ontos/owltable/", views.OwlTable.as_view(), name="onto_owltable"),
]
