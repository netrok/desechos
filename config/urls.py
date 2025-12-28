from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

from core.views import login_view, logout_view

urlpatterns = [
    # Home -> login (o cámbialo a /inventario/ si prefieres)
    path("", RedirectView.as_view(url="/login/", permanent=False)),

    # Admin
    path("admin/", admin.site.urls),

    # Auth custom
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),

    # Health
    path("health/", include("core.urls")),

    # API
    path("api/", include("inventario.api.urls")),

    # UI Inventario
    path("inventario/", include("inventario.web_urls")),

    # UI Ventas
    path("ventas/", include("ventas.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
