from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from rest_framework.routers import DefaultRouter

from .viewsets import (
    CategoriaViewSet,
    InventarioItemViewSet,
    MotivoBajaViewSet,
    UbicacionViewSet,
)

router = DefaultRouter()
router.register(r"categorias", CategoriaViewSet, basename="categorias")
router.register(r"ubicaciones", UbicacionViewSet, basename="ubicaciones")
router.register(r"motivos-baja", MotivoBajaViewSet, basename="motivos-baja")
router.register(r"items", InventarioItemViewSet, basename="items")


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "categorias": reverse("categorias-list", request=request, format=format),
            "ubicaciones": reverse("ubicaciones-list", request=request, format=format),
            "motivos_baja": reverse("motivos-baja-list", request=request, format=format),
            "items": reverse("items-list", request=request, format=format),
        }
    )


urlpatterns = [
    path("", api_root, name="api-root"),
    path("", include(router.urls)),
]
