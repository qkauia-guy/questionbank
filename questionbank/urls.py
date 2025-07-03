from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from quiz import views as quiz_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("quiz.urls")),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),  # 登出
    path("accounts/register/", quiz_views.register, name="register"),  # 註冊
]
