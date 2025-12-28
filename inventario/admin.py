from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Categoria,
    Ubicacion,
    MotivoBaja,
    InventarioItem,
    Producto,
    Articulo,
    ArticuloFoto,
    ArticuloEstado,
)


# ----------------------------
# Catálogos
# ----------------------------
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


# ----------------------------
# InventarioItem (interno)
# ----------------------------
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
        "etiqueta_interna",
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
        ("Equipo", {"fields": ("marca", "modelo")}),
        ("Responsable", {"fields": ("responsable",)}),
        ("Venta", {"fields": ("precio_sugerido_venta",)}),
        ("Detalles", {"fields": ("foto", "observaciones")}),
        ("Control", {"fields": ("activo", "fecha_alta", "fecha_baja", "motivo_baja")}),
    )

    def save_model(self, request, obj, form, change):
        # Si tu modelo ya hace full_clean() en save(), esto es redundante pero seguro.
        obj.full_clean()
        super().save_model(request, obj, form, change)


# ----------------------------
# Venta: catálogo / unidades
# ----------------------------
class ArticuloFotoInline(admin.TabularInline):
    model = ArticuloFoto
    extra = 1
    fields = ("orden", "imagen", "preview")
    readonly_fields = ("preview",)
    autocomplete_fields = ("articulo",)

    def preview(self, obj):
        if obj and obj.imagen:
            return format_html(
                '<img src="{}" style="height:60px;border-radius:8px;border:1px solid #ddd;" />',
                obj.imagen.url,
            )
        return "-"

    preview.short_description = "Vista"


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("sku", "nombre", "categoria", "precio_venta", "precio_minimo", "activo")
    search_fields = ("sku", "nombre", "marca", "modelo")
    list_filter = ("activo", "categoria")
    ordering = ("sku",)
    autocomplete_fields = ("categoria",)

    fieldsets = (
        ("Identidad", {"fields": ("sku", "nombre", "descripcion_venta")}),
        ("Clasificación", {"fields": ("categoria", "marca", "modelo", "activo")}),
        ("Precios", {"fields": ("costo", "precio_venta", "precio_minimo")}),
    )


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ("id", "producto", "serie", "etiqueta_interna", "estado", "ubicacion", "created_at", "created_by")
    search_fields = ("producto__sku", "producto__nombre", "serie", "etiqueta_interna")
    list_filter = ("estado", "ubicacion", "producto__categoria")
    ordering = ("-created_at", "-id")
    date_hierarchy = "created_at"
    autocomplete_fields = ("producto", "ubicacion")
    inlines = (ArticuloFotoInline,)

    actions = ("accion_disponible", "accion_reservado", "accion_vendido", "accion_baja", "accion_desecho")

    @admin.action(description="Estado -> DISPONIBLE")
    def accion_disponible(self, request, queryset):
        queryset.update(estado=ArticuloEstado.DISPONIBLE)

    @admin.action(description="Estado -> RESERVADO")
    def accion_reservado(self, request, queryset):
        queryset.update(estado=ArticuloEstado.RESERVADO)

    @admin.action(description="Estado -> VENDIDO")
    def accion_vendido(self, request, queryset):
        queryset.update(estado=ArticuloEstado.VENDIDO)

    @admin.action(description="Estado -> BAJA")
    def accion_baja(self, request, queryset):
        queryset.update(estado=ArticuloEstado.BAJA)

    @admin.action(description="Estado -> DESECHO")
    def accion_desecho(self, request, queryset):
        queryset.update(estado=ArticuloEstado.DESECHO)


@admin.register(ArticuloFoto)
class ArticuloFotoAdmin(admin.ModelAdmin):
    list_display = ("articulo", "orden", "imagen")
    ordering = ("articulo_id", "orden", "id")
    list_filter = ("articulo__producto",)
    search_fields = ("articulo__serie", "articulo__producto__sku")
    autocomplete_fields = ("articulo",)
