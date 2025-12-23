from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    # Home -> admin
    path("", RedirectView.as_view(url="/admin/", permanent=False)),

    path("admin/", admin.site.urls),

    # Health
    path("health/", include("core.urls")),

    # API
    path("api/", include("inventario.api.urls")),
]

# Media en desarrollo (fotos)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
