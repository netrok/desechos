from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from core.views import login_view, logout_view

urlpatterns = [
    # Home -> login
    path("", RedirectView.as_view(url="/login/", permanent=False)),

    # Admin (NO se envuelve con decoradores)
    path("admin/", admin.site.urls),

    # Health check (si tu core.urls lo maneja)
    path("health/", include("core.urls")),

    # API
    path("api/", include("inventario.api.urls")),

    # UI inventario
    path("inventario/", include("inventario.web_urls")),

    # Login/Logout custom
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
