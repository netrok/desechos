from __future__ import annotations

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

    # Nuevo
    codigo = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    foto = models.ImageField(upload_to="inventario/items/", null=True, blank=True)

    # Lo que te faltaba (catálogos + datos)
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    ubicacion = models.ForeignKey(Ubicacion, on_delete=models.PROTECT)
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.ALMACEN)

    marca = models.CharField(max_length=80, blank=True)
    modelo = models.CharField(max_length=120, blank=True)
    serie = models.CharField(max_length=120, blank=True, db_index=True)
    etiqueta_interna = models.CharField(max_length=60, blank=True, db_index=True)

    responsable = models.CharField(max_length=120, blank=True)
    observaciones = models.TextField(blank=True)

    fecha_alta = models.DateField(auto_now_add=True)
    fecha_baja = models.DateField(null=True, blank=True)

    motivo_baja = models.ForeignKey(
        MotivoBaja, null=True, blank=True, on_delete=models.PROTECT, related_name="items"
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
        return f"{self.codigo} - {self.categoria} - {base} ({serie})"
