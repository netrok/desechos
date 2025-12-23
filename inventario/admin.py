from django.contrib import admin
from .models import Categoria, Ubicacion, MotivoBaja, InventarioItem


@admin.register(InventarioItem)
class InventarioItemAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "categoria",
        "marca",
        "modelo",
        "serie",
        "estado",
        "ubicacion",
        "activo",
        "fecha_alta",
        "fecha_baja",
    )
    list_filter = ("categoria", "estado", "ubicacion", "activo")
    search_fields = ("codigo", "serie", "etiqueta_interna", "marca", "modelo", "responsable")
    list_per_page = 25


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)
    ordering = ("nombre",)


@admin.register(MotivoBaja)
class MotivoBajaAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)
    ordering = ("nombre",)
