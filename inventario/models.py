from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ("nombre",)

    def __str__(self) -> str:
        return self.nombre


class Ubicacion(models.Model):
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Ubicación"
        verbose_name_plural = "Ubicaciones"
        ordering = ("nombre",)

    def __str__(self) -> str:
        return self.nombre


class MotivoBaja(models.Model):
    nombre = models.CharField(max_length=120, unique=True)

    class Meta:
        verbose_name = "Motivo de baja"
        verbose_name_plural = "Motivos de baja"
        ordering = ("nombre",)

    def __str__(self) -> str:
        return self.nombre


class InventarioItem(models.Model):
    class Estado(models.TextChoices):
        EN_USO = "EN_USO", "En uso"
        ALMACEN = "ALMACEN", "Almacén"
        BAJA = "BAJA", "Baja"
        DESECHO = "DESECHO", "Desecho"

    # BD lo genera (SIS001, SIS002...) -> Django no lo exige en forms/admin/API
    codigo = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        editable=False,
        blank=True,
    )

    foto = models.ImageField(upload_to="inventario/items/", blank=True, null=True)

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ALMACEN)

    marca = models.CharField(max_length=80, blank=True)
    modelo = models.CharField(max_length=120, blank=True)
    serie = models.CharField(max_length=120, blank=True, db_index=True)
    etiqueta_interna = models.CharField(max_length=60, blank=True, db_index=True)

    responsable = models.CharField(max_length=120, blank=True)
    observaciones = models.TextField(blank=True)

    precio_sugerido_venta = models.DecimalField(
        "Precio sugerido de venta",
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    fecha_alta = models.DateField(auto_now_add=True)
    fecha_baja = models.DateField(blank=True, null=True)

    motivo_baja = models.ForeignKey(
        MotivoBaja,
        on_delete=models.PROTECT,
        related_name="items",
        blank=True,
        null=True,
    )

    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Item de inventario"
        verbose_name_plural = "Items de inventario"
        ordering = ("-fecha_alta", "-id")
        indexes = [
            models.Index(fields=["codigo"], name="inventario_codigo_idx"),
            models.Index(fields=["serie"], name="inventario_serie_idx"),
            models.Index(fields=["etiqueta_interna"], name="inventario_etiqueta_idx"),
        ]

    def __str__(self) -> str:
        return self.codigo or f"Item #{self.id}"

    def clean(self):
        super().clean()

        # 1) Estado manda sobre activo (sin contradicciones)
        if self.estado in (self.Estado.BAJA, self.Estado.DESECHO):
            self.activo = False

        # 2) Si NO está activo => exige fecha_baja y motivo_baja
        if self.activo is False:
            errors = {}
            if not self.fecha_baja:
                errors["fecha_baja"] = "Requerido cuando el equipo está dado de baja."
            if not self.motivo_baja_id:
                errors["motivo_baja"] = "Requerido cuando el equipo está dado de baja."
            if errors:
                raise ValidationError(errors)

        # 3) Si está activo => limpia baja (evita basura)
        if self.activo is True:
            self.fecha_baja = None
            self.motivo_baja = None

        # 4) Validación fechas
        if self.fecha_baja and self.fecha_alta and self.fecha_baja < self.fecha_alta:
            raise ValidationError({"fecha_baja": "No puede ser menor a la fecha de alta."})
