"""Root URL configuration."""
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path


urlpatterns = [
    # Built-in auth views give us hardened login / logout / password flows
    # without us writing any auth-handling code ourselves.
    path("accounts/login/",
         auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/",
         auth_views.LogoutView.as_view(), name="logout"),
    path("accounts/password_change/",
         auth_views.PasswordChangeView.as_view(), name="password_change"),
    path("accounts/password_change/done/",
         auth_views.PasswordChangeDoneView.as_view(), name="password_change_done"),
    path("accounts/password_reset/",
         auth_views.PasswordResetView.as_view(), name="password_reset"),
    path("accounts/password_reset/done/",
         auth_views.PasswordResetDoneView.as_view(), name="password_reset_done"),
    path("accounts/reset/<uidb64>/<token>/",
         auth_views.PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("accounts/reset/done/",
         auth_views.PasswordResetCompleteView.as_view(), name="password_reset_complete"),

    path("admin/", admin.site.urls),
    path("", include("core.urls")),
]
