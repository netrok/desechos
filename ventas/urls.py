# ventas/urls.py
from django.urls import path
from . import web_views

app_name = "ventas"

urlpatterns = [
    path("", web_views.ventas_list, name="ventas_list"),

    # Clientes
    path("clientes/", web_views.clientes_list, name="clientes_list"),
    path("clientes/nuevo/", web_views.cliente_create, name="cliente_create"),

    # Ventas
    path("nueva/", web_views.venta_create, name="venta_create"),
    path("<int:venta_id>/", web_views.venta_detail, name="venta_detail"),

    # Detalles
    path("<int:venta_id>/detalles/agregar/", web_views.venta_add_detalle, name="venta_add_detalle"),
    path("<int:venta_id>/detalles/<int:detalle_id>/eliminar/", web_views.venta_delete_detalle, name="venta_delete_detalle"),

    # Pagos
    path("<int:venta_id>/pagos/agregar/", web_views.venta_add_pago, name="venta_add_pago"),

    # Acciones
    path("<int:venta_id>/accion/<str:action>/", web_views.venta_action, name="venta_action"),
]
