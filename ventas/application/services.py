# ventas/application/services.py
from __future__ import annotations

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from inventario.models import Articulo, ArticuloEstado
from ventas.models import Venta, VentaEstado, Pago


@transaction.atomic
def recalcular_totales(venta: Venta) -> Venta:
    """
    Recalcula subtotal/descuento/impuestos/total usando el método centralizado del modelo.
    Esto evita duplicar lógica en services/admin/signals.
    """
    venta = Venta.objects.select_for_update().get(pk=venta.pk)
    Venta.recalcular_totales_por_id(venta.id)
    venta.refresh_from_db(fields=["subtotal", "descuento", "impuestos", "total"])
    return venta


@transaction.atomic
def reservar_articulos(venta: Venta) -> Venta:
    """
    BORRADOR -> RESERVADO (solo si estaban DISPONIBLE).
    Con locks para evitar carreras.
    """
    venta = Venta.objects.select_for_update().get(pk=venta.pk)

    if venta.estado != VentaEstado.BORRADOR:
        raise ValidationError("Solo puedes reservar una venta en BORRADOR.")

    articulo_ids = list(venta.detalles.values_list("articulo_id", flat=True))
    if not articulo_ids:
        raise ValidationError("La venta no tiene artículos.")

    articulos = list(
        Articulo.objects.select_for_update()
        .filter(id__in=articulo_ids)
        .only("id", "estado")
    )

    for a in articulos:
        if a.estado != ArticuloEstado.DISPONIBLE:
            raise ValidationError(f"Artículo {a.id} no disponible (estado={a.estado}).")

    Articulo.objects.filter(id__in=articulo_ids).update(estado=ArticuloEstado.RESERVADO)
    return venta


@transaction.atomic
def marcar_pagada(
    venta: Venta,
    metodo: str,
    monto: Decimal,
    referencia: str = "",
    exigir_reservado: bool = False,
) -> Venta:
    """
    Registra pago y marca la venta PAGADA si pagos >= total.
    Cambia artículos a VENDIDO con locks.
    """
    venta = Venta.objects.select_for_update().get(pk=venta.pk)

    if venta.estado == VentaEstado.CANCELADA:
        raise ValidationError("No puedes pagar una venta CANCELADA.")
    if venta.estado == VentaEstado.ENTREGADA:
        raise ValidationError("No puedes pagar una venta ENTREGADA.")
    if monto is None or monto < Decimal("0.00"):
        raise ValidationError("Monto inválido.")

    # Totales al día (y lock de la venta ya tomado)
    venta = recalcular_totales(venta)

    articulo_ids = list(venta.detalles.values_list("articulo_id", flat=True))
    if not articulo_ids:
        raise ValidationError("La venta no tiene artículos.")

    # Lock de artículos
    articulos = list(
        Articulo.objects.select_for_update()
        .filter(id__in=articulo_ids)
        .only("id", "estado")
    )

    for a in articulos:
        if a.estado == ArticuloEstado.VENDIDO:
            raise ValidationError(f"Artículo {a.id} ya está VENDIDO.")
        if a.estado == ArticuloEstado.BAJA:
            raise ValidationError(f"Artículo {a.id} está en BAJA.")
        if exigir_reservado and a.estado != ArticuloEstado.RESERVADO:
            raise ValidationError(f"Artículo {a.id} debe estar RESERVADO (estado={a.estado}).")
        if not exigir_reservado and a.estado not in (ArticuloEstado.RESERVADO, ArticuloEstado.DISPONIBLE):
            raise ValidationError(f"Artículo {a.id} no puede venderse (estado={a.estado}).")

    # Crear pago
    Pago.objects.create(venta=venta, metodo=metodo, monto=monto, referencia=referencia)

    # Recalcular pagado DESPUÉS de crear el pago (ya dentro de la misma transacción)
    pagado = venta.pagos.aggregate(s=Sum("monto"))["s"] or Decimal("0.00")
    if pagado < (venta.total or Decimal("0.00")):
        raise ValidationError("Pagos insuficientes para marcar como PAGADA.")

    # Vender artículos
    Articulo.objects.filter(id__in=articulo_ids).update(estado=ArticuloEstado.VENDIDO)

    venta.estado = VentaEstado.PAGADA
    venta.pagada_en = venta.pagada_en or timezone.now()
    venta.save(update_fields=["estado", "pagada_en"])
    return venta


@transaction.atomic
def cancelar_venta(venta: Venta) -> Venta:
    """
    Cancela venta y libera artículos RESERVADO -> DISPONIBLE.
    """
    venta = Venta.objects.select_for_update().get(pk=venta.pk)

    if venta.estado == VentaEstado.CANCELADA:
        return venta

    if venta.estado in (VentaEstado.PAGADA, VentaEstado.ENTREGADA):
        raise ValidationError("No puedes cancelar una venta PAGADA/ENTREGADA (haz devolución después).")

    articulo_ids = list(venta.detalles.values_list("articulo_id", flat=True))
    if not articulo_ids:
        venta.estado = VentaEstado.CANCELADA
        venta.save(update_fields=["estado"])
        return venta

    # Lock de artículos
    Articulo.objects.select_for_update().filter(id__in=articulo_ids)

    # Libera solo reservados
    Articulo.objects.filter(id__in=articulo_ids, estado=ArticuloEstado.RESERVADO).update(
        estado=ArticuloEstado.DISPONIBLE
    )

    venta.estado = VentaEstado.CANCELADA
    venta.save(update_fields=["estado"])
    return venta


@transaction.atomic
def marcar_entregada(venta: Venta) -> Venta:
    """
    Entrega solo si está PAGADA.
    """
    venta = Venta.objects.select_for_update().get(pk=venta.pk)

    if venta.estado != VentaEstado.PAGADA:
        raise ValidationError("Solo puedes entregar una venta PAGADA.")

    venta.estado = VentaEstado.ENTREGADA
    venta.entregada_en = venta.entregada_en or timezone.now()
    venta.save(update_fields=["estado", "entregada_en"])
    return venta
