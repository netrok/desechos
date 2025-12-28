from __future__ import annotations

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from .application.services import (
    recalcular_totales,
    reservar_articulos,
    marcar_pagada,
    cancelar_venta,
    marcar_entregada,
)
from .forms import ClienteForm, VentaCreateForm, VentaDetalleForm, PagoForm
from .models import Cliente, Venta, VentaEstado, MetodoPago


# ----------------------------
# Ventas (listado)
# ----------------------------
@login_required
@require_http_methods(["GET"])
def ventas_list(request):
    q = (request.GET.get("q") or "").strip()
    estado = (request.GET.get("estado") or "").strip()

    ventas = Venta.objects.select_related("cliente", "vendedor").order_by("-creada_en", "-id")

    if q:
        ventas = ventas.filter(
            Q(cliente__nombre__icontains=q) | Q(folio__icontains=q)
        ).distinct()

    if estado:
        ventas = ventas.filter(estado=estado)

    return render(
        request,
        "ventas/ventas_list.html",
        {
            "ventas": ventas[:300],  # simple: límite para no reventar
            "q": q,
            "estado": estado,
            "estados": VentaEstado.choices,
        },
    )


# ----------------------------
# Clientes (listado + alta)
# ----------------------------
@login_required
@require_http_methods(["GET"])
def clientes_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = Cliente.objects.order_by("nombre")
    if q:
        qs = qs.filter(nombre__icontains=q)
    return render(request, "ventas/clientes_list.html", {"clientes": qs[:500], "q": q})


@login_required
@require_http_methods(["GET", "POST"])
def cliente_create(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Cliente creado.")
            return redirect("ventas:clientes_list")
        messages.error(request, "Revisa el formulario.")
    else:
        form = ClienteForm()

    return render(request, "ventas/cliente_form.html", {"form": form})


# ----------------------------
# Venta (crear + detalle)
# ----------------------------
@login_required
@require_http_methods(["GET", "POST"])
def venta_create(request):
    if request.method == "POST":
        form = VentaCreateForm(request.POST)
        if form.is_valid():
            venta = form.save(commit=False)
            venta.vendedor = request.user
            venta.save()
            messages.success(request, f"Venta creada ({venta.folio or 'sin folio aún'}).")
            return redirect("ventas:venta_detail", venta_id=venta.id)
        messages.error(request, "Revisa el formulario.")
    else:
        form = VentaCreateForm()

    return render(request, "ventas/venta_form.html", {"form": form})


@login_required
@require_http_methods(["GET"])
def venta_detail(request, venta_id: int):
    venta = get_object_or_404(
        Venta.objects.select_related("cliente", "vendedor").prefetch_related("detalles__articulo__producto", "pagos"),
        pk=venta_id,
    )

    detalle_form = VentaDetalleForm(venta=venta)
    pago_form = PagoForm()

    return render(
        request,
        "ventas/venta_detail.html",
        {
            "venta": venta,
            "detalle_form": detalle_form,
            "pago_form": pago_form,
        },
    )


# ----------------------------
# Detalles
# ----------------------------
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def venta_add_detalle(request, venta_id: int):
    venta = get_object_or_404(Venta, pk=venta_id)

    form = VentaDetalleForm(request.POST, venta=venta)
    if form.is_valid():
        det = form.save(commit=False)
        det.venta = venta
        det.save()  # recalcula por hooks (on_commit)
        messages.success(request, "Artículo agregado a la venta.")
    else:
        messages.error(request, "No se pudo agregar el artículo. Revisa los datos.")

    return redirect("ventas:venta_detail", venta_id=venta.id)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def venta_delete_detalle(request, venta_id: int, detalle_id: int):
    venta = get_object_or_404(Venta, pk=venta_id)
    det = get_object_or_404(venta.detalles, pk=detalle_id)
    det.delete()
    messages.success(request, "Detalle eliminado.")
    return redirect("ventas:venta_detail", venta_id=venta.id)


# ----------------------------
# Pagos
# ----------------------------
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def venta_add_pago(request, venta_id: int):
    venta = get_object_or_404(Venta, pk=venta_id)

    form = PagoForm(request.POST)
    if form.is_valid():
        pago = form.save(commit=False)
        pago.venta = venta
        pago.save()  # recalcula por hooks (on_commit)
        messages.success(request, "Pago registrado.")
    else:
        messages.error(request, "Pago inválido.")

    return redirect("ventas:venta_detail", venta_id=venta.id)


# ----------------------------
# Acciones: reservar / pagar / entregar / cancelar / recalcular
# ----------------------------
@login_required
@require_http_methods(["POST"])
@transaction.atomic
def venta_action(request, venta_id: int, action: str):
    venta = get_object_or_404(Venta, pk=venta_id)

    try:
        if action == "recalcular":
            recalcular_totales(venta)
            messages.success(request, "Totales recalculados.")

        elif action == "reservar":
            reservar_articulos(venta)
            messages.success(request, "Artículos reservados.")

        elif action == "pagar_efectivo":
            recalcular_totales(venta)
            total = Decimal(venta.total or Decimal("0.00"))
            marcar_pagada(venta, metodo=MetodoPago.EFECTIVO, monto=total, referencia="")
            messages.success(request, "Venta marcada como PAGADA (efectivo).")

        elif action == "entregar":
            marcar_entregada(venta)
            messages.success(request, "Venta marcada como ENTREGADA.")

        elif action == "cancelar":
            cancelar_venta(venta)
            messages.success(request, "Venta cancelada.")

        else:
            messages.error(request, "Acción no soportada.")

    except ValidationError as e:
        # Django puede mandar dict/lista/string, lo normalizamos
        msg = getattr(e, "message_dict", None) or getattr(e, "messages", None) or [str(e)]
        messages.error(request, f"Validación: {msg}")

    except Exception as e:
        messages.error(request, f"Error: {e}")

    return redirect("ventas:venta_detail", venta_id=venta.id)
