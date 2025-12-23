from django.urls import path
from . import web_views

app_name = "inventario_ui"

urlpatterns = [
    path("", web_views.item_list, name="item_list"),
    path("items/nuevo/", web_views.item_create, name="item_create"),
    path("items/<int:pk>/", web_views.item_detail, name="item_detail"),
    path("items/<int:pk>/editar/", web_views.item_update, name="item_update"),
    path("items/<int:pk>/baja/", web_views.item_baja, name="item_baja"),
]
