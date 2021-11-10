from django.urls import path
from django.urls import path
from . import views

urlpatterns = [
    path("register/", views.RegisterUser.as_view(), name="register"),
    path("login/", views.LoginUser.as_view(), name="login"),
    path("reset_password/", views.PasswordResetEmail.as_view(),
         name="reset_password"),
    path(
        "reset_password_confirm/",
        views.PasswordResetConfirm.as_view(),
        name="reset_confirm",
    ),
]
