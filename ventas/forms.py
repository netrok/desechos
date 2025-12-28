from __future__ import annotations

from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from inventario.models import Articulo, ArticuloEstado
from .models import Cliente, Venta, VentaDetalle, Pago, MetodoPago


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ("nombre", "telefono", "email", "rfc", "direccion")


class VentaCreateForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ("cliente",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cliente"].queryset = Cliente.objects.order_by("nombre")


class VentaDetalleForm(forms.ModelForm):
    class Meta:
        model = VentaDetalle
        fields = ("articulo", "precio", "descuento")

    def __init__(self, *args, **kwargs):
        venta: Venta | None = kwargs.pop("venta", None)
        super().__init__(*args, **kwargs)

        # Solo artículos disponibles para agregar a la venta
        qs = Articulo.objects.select_related("producto").filter(estado=ArticuloEstado.DISPONIBLE)
        self.fields["articulo"].queryset = qs.order_by("-created_at")

        # Si quieres permitir agregar artículos ya RESERVADO (por flujo), agrégalo aquí:
        # qs = Articulo.objects.filter(estado__in=[ArticuloEstado.DISPONIBLE, ArticuloEstado.RESERVADO])

        self.venta = venta

    def clean(self):
        cleaned = super().clean()
        articulo = cleaned.get("articulo")

        # OneToOne ya evita duplicados, pero mejor dar error claro
        if articulo and hasattr(articulo, "venta_detalle"):
            raise ValidationError({"articulo": "Este artículo ya está en otra venta."})

        return cleaned


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ("metodo", "monto", "referencia")

    def clean_monto(self):
        monto = self.cleaned_data.get("monto")
        if monto is None:
            return monto
        if monto < Decimal("0.00"):
            raise ValidationError("El monto no puede ser negativo.")
        return monto
