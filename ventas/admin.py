# ventas/admin.py
from __future__ import annotations

from decimal import Decimal

from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Cliente, Venta, VentaDetalle, Pago, VentaEstado, MetodoPago
from .application.services import (
    recalcular_totales,
    reservar_articulos,
    marcar_pagada,
    cancelar_venta,
    marcar_entregada,
)


# ----------------------------
# Catálogo: Clientes
# ----------------------------
@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    search_fields = ("nombre", "telefono", "email", "rfc")
    list_display = ("nombre", "telefono", "email", "rfc")
    ordering = ("nombre",)


# ----------------------------
# Inlines
# ----------------------------
class VentaDetalleInline(admin.TabularInline):
    model = VentaDetalle
    extra = 0
    autocomplete_fields = ("articulo",)
    fields = ("articulo", "precio", "descuento")
    show_change_link = True


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    fields = ("metodo", "monto", "referencia", "fecha")
    readonly_fields = ("fecha",)


# ----------------------------
# Admin: Ventas
# ----------------------------
@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    inlines = (VentaDetalleInline, PagoInline)

    list_display = ("folio", "cliente", "estado", "total", "creada_en", "pagada_en", "entregada_en", "vendedor")
    list_filter = ("estado", "creada_en")
    search_fields = ("folio", "cliente__nombre", "cliente__telefono", "cliente__email")
    ordering = ("-creada_en", "-id")
    date_hierarchy = "creada_en"

    readonly_fields = (
        "folio",
        "creada_en",
        "pagada_en",
        "entregada_en",
        "subtotal",
        "descuento",
        "impuestos",
        "total",
    )
    autocomplete_fields = ("cliente",)

    actions = (
        "accion_recalcular",
        "accion_reservar",
        "accion_marcar_pagada_efectivo",
        "accion_marcar_entregada",
        "accion_cancelar",
    )

    def save_model(self, request, obj, form, change):
        obj.full_clean()
        super().save_model(request, obj, form, change)

    @admin.action(description="Recalcular totales")
    def accion_recalcular(self, request, queryset):
        ok, fail = 0, 0
        for v in queryset:
            try:
                recalcular_totales(v)
                ok += 1
            except Exception:
                fail += 1
        if ok:
            messages.success(request, f"Totales recalculados para {ok} venta(s).")
        if fail:
            messages.error(request, f"Fallaron {fail} venta(s) al recalcular (revisa detalles/reglas).")

    @admin.action(description="Reservar artículos (solo BORRADOR)")
    def accion_reservar(self, request, queryset):
        ok, skip, fail = 0, 0, 0
        for v in queryset:
            if v.estado != VentaEstado.BORRADOR:
                skip += 1
                continue
            try:
                reservar_articulos(v)
                ok += 1
            except ValidationError:
                fail += 1
            except Exception:
                fail += 1

        if ok:
            messages.success(request, f"Reservadas: {ok}.")
        if skip:
            messages.warning(request, f"Omitidas (no BORRADOR): {skip}.")
        if fail:
            messages.error(request, f"Fallaron al reservar: {fail}.")

    @admin.action(description="Marcar PAGADA (EFECTIVO = total)")
    def accion_marcar_pagada_efectivo(self, request, queryset):
        ok, fail = 0, 0
        for v in queryset:
            try:
                recalcular_totales(v)
                total = v.total or Decimal("0.00")
                marcar_pagada(v, metodo=MetodoPago.EFECTIVO, monto=total, referencia="")
                ok += 1
            except ValidationError:
                fail += 1
            except Exception:
                fail += 1

        if ok:
            messages.success(request, f"Pagadas: {ok}.")
        if fail:
            messages.error(request, f"Fallaron: {fail} (pagos insuficientes, sin detalles, artículo no disponible, etc.).")

    @admin.action(description="Marcar ENTREGADA (solo PAGADA)")
    def accion_marcar_entregada(self, request, queryset):
        ok, skip, fail = 0, 0, 0
        for v in queryset:
            if v.estado != VentaEstado.PAGADA:
                skip += 1
                continue
            try:
                marcar_entregada(v)
                ok += 1
            except ValidationError:
                fail += 1
            except Exception:
                fail += 1

        if ok:
            messages.success(request, f"Entregadas: {ok}.")
        if skip:
            messages.warning(request, f"Omitidas (no PAGADA): {skip}.")
        if fail:
            messages.error(request, f"Fallaron: {fail}.")

    @admin.action(description="Cancelar venta (solo BORRADOR)")
    def accion_cancelar(self, request, queryset):
        ok, skip, fail = 0, 0, 0
        with transaction.atomic():
            for v in queryset.select_for_update():
                if v.estado != VentaEstado.BORRADOR:
                    skip += 1
                    continue
                try:
                    cancelar_venta(v)
                    ok += 1
                except ValidationError:
                    fail += 1
                except Exception:
                    fail += 1

        if ok:
            messages.success(request, f"Canceladas: {ok}.")
        if skip:
            messages.warning(request, f"Omitidas (no BORRADOR): {skip}.")
        if fail:
            messages.error(request, f"Fallaron: {fail}.")


# ----------------------------
# Admin: Detalles y Pagos
# ----------------------------
@admin.register(VentaDetalle)
class VentaDetalleAdmin(admin.ModelAdmin):
    list_display = ("venta", "articulo", "precio", "descuento")
    search_fields = ("venta__folio", "articulo__serie", "articulo__etiqueta_interna", "articulo__producto__sku")
    autocomplete_fields = ("venta", "articulo")


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ("venta", "metodo", "monto", "referencia", "fecha")
    list_filter = ("metodo", "fecha")
    search_fields = ("venta__folio", "referencia")
    autocomplete_fields = ("venta",)
