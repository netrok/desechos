from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from django.contrib.admin.views.decorators import staff_member_required  # Importa el decorador adecuado
from core.views import login_view, logout_view  # Asegúrate de importar las vistas

# URLs del proyecto
urlpatterns = [
    # Redirige a login si no hay sesión activa
    path("", RedirectView.as_view(url="/login/", permanent=False)),  # Redirige directo al login

    # Admin de Django (protegido con acceso solo para staff)
    path("admin/", staff_member_required(admin.site.urls)),  # Usamos staff_member_required para proteger la ruta

    # Health check
    path("health/", include("core.urls")),  # Incluye las rutas del health check desde 'core.urls'

    # API de Inventario
    path("api/", include("inventario.api.urls")),

    # UI interna de Inventario (con acceso solo para staff)
    path("inventario/", include("inventario.web_urls")),

    # Rutas personalizadas de Login/Logout
    path("login/", login_view, name="login"),  # Aquí va el login custom
    path("logout/", logout_view, name="logout"),  # Aquí va el logout
]

# Configuración para servir archivos estáticos y de medios durante el desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
