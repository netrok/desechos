from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.db.models import Sum

from inventario.models import ArticuloEstado


# ----------------------------
# Catálogo de clientes
# ----------------------------
class Cliente(models.Model):
    nombre = models.CharField(max_length=200)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    rfc = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)

    class Meta:
        ordering = ("nombre",)

    def __str__(self) -> str:
        return self.nombre


class VentaEstado(models.TextChoices):
    BORRADOR = "BORRADOR", "Borrador"
    PAGADA = "PAGADA", "Pagada"
    ENTREGADA = "ENTREGADA", "Entregada"
    CANCELADA = "CANCELADA", "Cancelada"


class MetodoPago(models.TextChoices):
    EFECTIVO = "EFECTIVO", "Efectivo"
    TRANSFERENCIA = "TRANSFERENCIA", "Transferencia"
    TARJETA = "TARJETA", "Tarjeta"


# ----------------------------
# Venta
# ----------------------------
class Venta(models.Model):
    # Lo generará la BD (trigger/sequence). Django no lo pide en forms/admin.
    folio = models.CharField(
        max_length=30,
        unique=True,
        db_index=True,
        editable=False,
        blank=True,
    )

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="ventas")
    estado = models.CharField(max_length=20, choices=VentaEstado.choices, default=VentaEstado.BORRADOR)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    impuestos = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    vendedor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)

    creada_en = models.DateTimeField(auto_now_add=True)
    pagada_en = models.DateTimeField(null=True, blank=True)
    entregada_en = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-creada_en", "-id")
        indexes = [
            models.Index(fields=["folio"]),
            models.Index(fields=["estado"]),
            models.Index(fields=["creada_en"]),
        ]

    def __str__(self) -> str:
        return self.folio or f"Venta #{self.pk or 'NUEVA'}"

    def clean(self):
        super().clean()
        errors = {}

        for field in ("subtotal", "descuento", "impuestos", "total"):
            val = getattr(self, field)
            if val is not None and val < 0:
                errors[field] = "No puede ser negativo."

        if errors:
            raise ValidationError(errors)

    @staticmethod
    def recalcular_totales_por_id(venta_id: int) -> None:
        """
        Recalcula subtotal/descuento/total en BD.
        - IVA/impuestos: 0 por ahora (luego lo metemos).
        """
        from ventas.models import VentaDetalle  # import local (OK)

        agg = VentaDetalle.objects.filter(venta_id=venta_id).aggregate(
            subtotal=Sum("precio"),
            descuento=Sum("descuento"),
        )

        subtotal = agg["subtotal"] or Decimal("0.00")
        descuento = agg["descuento"] or Decimal("0.00")

        impuestos = Decimal("0.00")
        total = subtotal - descuento + impuestos
        if total < 0:
            total = Decimal("0.00")

        Venta.objects.filter(pk=venta_id).update(
            subtotal=subtotal,
            descuento=descuento,
            impuestos=impuestos,
            total=total,
        )


# ----------------------------
# Detalle (líneas)
# ----------------------------
class VentaDetalle(models.Model):
    """
    Un Articulo SOLO puede estar en una venta (y por ende venderse una vez).
    """

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles")
    articulo = models.OneToOneField("inventario.Articulo", on_delete=models.PROTECT, related_name="venta_detalle")

    precio = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    descuento = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ("id",)
        indexes = [
            models.Index(fields=["venta"]),
            models.Index(fields=["articulo"]),
        ]

    def __str__(self) -> str:
        return f"{self.venta.folio or self.venta_id} - {self.articulo_id}"

    def clean(self):
        super().clean()
        errors = {}

        # Bloqueo duro: no disponible
        if self.articulo and self.articulo.estado in (
            ArticuloEstado.VENDIDO,
            ArticuloEstado.BAJA,
            ArticuloEstado.RESERVADO,  # si ya está reservado, alguien más lo apartó
        ):
            errors["articulo"] = f"Este artículo no está disponible (estado={self.articulo.estado})."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
        venta_id = self.venta_id
        transaction.on_commit(lambda: Venta.recalcular_totales_por_id(venta_id))

    def delete(self, *args, **kwargs):
        venta_id = self.venta_id
        super().delete(*args, **kwargs)
        transaction.on_commit(lambda: Venta.recalcular_totales_por_id(venta_id))


# ----------------------------
# Pagos
# ----------------------------
class Pago(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="pagos")
    metodo = models.CharField(max_length=20, choices=MetodoPago.choices)

    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    referencia = models.CharField(max_length=120, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-fecha", "-id")
        indexes = [
            models.Index(fields=["venta"]),
            models.Index(fields=["metodo"]),
        ]

    def __str__(self) -> str:
        return f"{self.venta.folio or self.venta_id} - {self.metodo} {self.monto}"

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

