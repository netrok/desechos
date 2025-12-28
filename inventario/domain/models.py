from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models


# ----------------------------
# Catálogos
# ----------------------------
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


# ----------------------------
# Inventario (interno)
# ----------------------------
class InventarioItem(models.Model):
    class Estado(models.TextChoices):
        EN_USO = "EN_USO", "En uso"
        ALMACEN = "ALMACEN", "Almacén"
        BAJA = "BAJA", "Baja"
        DESECHO = "DESECHO", "Desecho"

    # Si lo generas en BD con trigger/sequence: déjalo blank=True y editable=False.
    # OJO: Django insertará '' (cadena vacía), así que tu trigger debe considerar '' como "sin código".
    codigo = models.CharField(max_length=20, unique=True, editable=False, db_index=True, blank=True)

    foto = models.ImageField(upload_to="inventario/items/", null=True, blank=True)

    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="items")
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT, related_name="items")
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
    fecha_baja = models.DateField(null=True, blank=True)

    motivo_baja = models.ForeignKey(
        MotivoBaja,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="items",
    )

    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Item de inventario"
        verbose_name_plural = "Items de inventario"
        ordering = ("-fecha_alta", "-id")
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["serie"]),
            models.Index(fields=["etiqueta_interna"]),
        ]

    def __str__(self) -> str:
        base = f"{(self.marca or '').strip()} {(self.modelo or '').strip()}".strip() or "Sin descripción"
        serie = self.serie.strip() if self.serie else "sin serie"
        codigo = self.codigo or (f"Item #{self.pk}" if self.pk else "Item (sin guardar)")
        return f"{codigo} - {self.categoria} - {base} ({serie})"

    def clean(self) -> None:
        super().clean()

        # Estado manda sobre activo
        if self.estado in (self.Estado.BAJA, self.Estado.DESECHO):
            self.activo = False

        # Si está activo, limpia campos de baja
        if self.activo:
            self.fecha_baja = None
            self.motivo_baja = None
            return

        # Si NO está activo, exige baja completa
        errors: dict[str, str] = {}
        if not self.fecha_baja:
            errors["fecha_baja"] = "Requerido cuando el equipo está dado de baja."
        if not self.motivo_baja_id:
            errors["motivo_baja"] = "Requerido cuando el equipo está dado de baja."
        if errors:
            raise ValidationError(errors)

        if self.fecha_baja and self.fecha_alta and self.fecha_baja < self.fecha_alta:
            raise ValidationError({"fecha_baja": "No puede ser menor a la fecha de alta."})

    def save(self, *args, **kwargs):
        # Para que reglas apliquen siempre (no solo en admin/forms)
        self.full_clean()
        return super().save(*args, **kwargs)


# ----------------------------
# Venta (catálogo vs unidades)
# ----------------------------
class Producto(models.Model):
    """
    Producto = lo que publicas / vendes como 'modelo' (SKU)
    Ej: 'LAP-DELL-5400-I5-16-512'
    """

    sku = models.CharField(max_length=50, unique=True, db_index=True)
    nombre = models.CharField(max_length=200)
    descripcion_venta = models.TextField(blank=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
        null=True,
        blank=True,
    )
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=120, blank=True)

    costo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    precio_venta = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    precio_minimo = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("sku",)
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["nombre"]),
        ]

    def __str__(self) -> str:
        return f"{self.sku} - {self.nombre}"


class ArticuloEstado(models.TextChoices):
    DISPONIBLE = "DISPONIBLE", "Disponible"
    RESERVADO = "RESERVADO", "Reservado"
    VENDIDO = "VENDIDO", "Vendido"
    REPARACION = "REPARACION", "En reparación"
    BAJA = "BAJA", "Baja"
    DESECHO = "DESECHO", "Desecho"


class Articulo(models.Model):
    """
    Artículo = unidad física (normalmente con serie)
    """

    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, related_name="articulos")

    serie = models.CharField(max_length=120, blank=True, null=True, db_index=True)
    etiqueta_interna = models.CharField(max_length=60, blank=True, db_index=True)

    condicion = models.CharField(max_length=50, blank=True)  # Nuevo / Usado / Refurb / Partes
    grado = models.CharField(max_length=10, blank=True)      # A/B/C o 10/10
    accesorios = models.CharField(max_length=200, blank=True)

    ubicacion = models.ForeignKey(
        Ubicacion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="articulos",
    )
    estado = models.CharField(max_length=20, choices=ArticuloEstado.choices, default=ArticuloEstado.DISPONIBLE)

    observaciones = models.TextField(blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["estado"]),
            models.Index(fields=["serie"]),
            models.Index(fields=["etiqueta_interna"]),
        ]
        # Permite múltiples NULL y múltiples '' (vacíos). Solo restringe series reales.
        constraints = [
            models.UniqueConstraint(
                fields=["serie"],
                name="uniq_articulo_serie",
                condition=~models.Q(serie__isnull=True) & ~models.Q(serie=""),
            ),
        ]

    def __str__(self) -> str:
        return f"{self.producto.sku} / {self.serie or 'SIN SERIE'} ({self.estado})"


class ArticuloFoto(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name="fotos")
    imagen = models.ImageField(upload_to="inventario/articulos/")
    orden = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ("orden", "id")

    def __str__(self) -> str:
        return f"Foto #{self.orden} - {self.articulo_id}"
