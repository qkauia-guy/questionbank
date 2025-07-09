from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings  # ✅ 補上
from django.conf.urls.static import static  # ✅ 補上
from quiz import views as quiz_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("quiz.urls")),
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(next_page="login"),
        name="logout",
    ),
    path("accounts/register/", quiz_views.register, name="register"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
