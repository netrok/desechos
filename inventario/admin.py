from django.contrib import admin
from .models import Categoria, Ubicacion, MotivoBaja, InventarioItem


@admin.register(InventarioItem)
class InventarioItemAdmin(admin.ModelAdmin):
    list_display = (
        "codigo",
        "categoria",
        "ubicacion",
        "estado",
        "activo",
        "marca",
        "modelo",
        "serie",
        "precio_sugerido_venta",
        "fecha_alta",
        "fecha_baja",
        "motivo_baja",
    )
    list_display_links = ("codigo", "modelo")
    list_select_related = ("categoria", "ubicacion", "motivo_baja")

    list_filter = ("activo", "categoria", "estado", "ubicacion", "motivo_baja")
    search_fields = (
        "codigo",
        "serie",
        "etiqueta_interna",
        "marca",
        "modelo",
        "responsable",
        "observaciones",
    )
    ordering = ("-fecha_alta", "codigo")
    list_per_page = 25
    date_hierarchy = "fecha_alta"

    # BD manda: codigo se genera solo (SIS001, SIS002, ...)
    readonly_fields = ("codigo", "fecha_alta")

    autocomplete_fields = ("categoria", "ubicacion", "motivo_baja")

    fieldsets = (
        ("Identificación", {"fields": ("codigo", "etiqueta_interna", "serie")}),
        ("Clasificación", {"fields": ("categoria", "ubicacion", "estado")}),
        ("Equipo", {"fields": ("marca", "modelo",)}),
        ("Responsable", {"fields": ("responsable",)}),
        ("Venta", {"fields": ("precio_sugerido_venta",)}),
        ("Detalles", {"fields": ("foto", "observaciones")}),
        ("Control", {"fields": ("activo", "fecha_alta", "fecha_baja", "motivo_baja")}),
    )

    def save_model(self, request, obj, form, change):
        # Fuerza validaciones del modelo (incluye reglas de baja)
        obj.full_clean()
        super().save_model(request, obj, form, change)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)
    ordering = ("nombre",)
    list_display = ("nombre",)


@admin.register(Ubicacion)
class UbicacionAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)
    ordering = ("nombre",)
    list_display = ("nombre",)


@admin.register(MotivoBaja)
class MotivoBajaAdmin(admin.ModelAdmin):
    search_fields = ("nombre",)
    ordering = ("nombre",)
    list_display = ("nombre",)
