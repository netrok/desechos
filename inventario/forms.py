from __future__ import annotations

from django import forms
from .models import InventarioItem


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for _, field in self.fields.items():
            w = field.widget

            if isinstance(w, forms.CheckboxInput):
                w.attrs.setdefault("class", "form-check-input")
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs.setdefault("class", "form-select")
            elif isinstance(w, forms.Textarea):
                w.attrs.setdefault("class", "form-control")
                w.attrs.setdefault("rows", 3)
            elif isinstance(w, forms.ClearableFileInput):
                w.attrs.setdefault("class", "form-control")
            else:
                w.attrs.setdefault("class", "form-control")


def _model_has_field(model, field_name: str) -> bool:
    try:
        model._meta.get_field(field_name)
        return True
    except Exception:
        return False


class InventarioItemForm(BootstrapModelForm):
    """
    Alta/Edición: NO se permite BAJA/DESECHO aquí.
    La baja se hace en su pantalla (InventarioBajaForm).
    """

    class Meta:
        model = InventarioItem
        fields = [
            "foto",
            "categoria",
            "ubicacion",
            "estado",
            "marca",
            "modelo",
            "serie",
            "etiqueta_interna",
            "responsable",
            "observaciones",
            # Nota: lo agregamos dinámicamente en __init__ solo si existe en el modelo
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Agrega precio_sugerido_venta solo si el modelo lo tiene
        if _model_has_field(InventarioItem, "precio_sugerido_venta"):
            self.fields["precio_sugerido_venta"] = forms.DecimalField(
                required=False,
                min_value=0,
                decimal_places=2,
                max_digits=12,
                widget=forms.NumberInput(attrs={"step": "0.01", "min": "0"}),
                label="Precio sugerido de venta",
            )

            # Si ya viene en instance, precárgalo
            if self.instance and getattr(self.instance, "pk", None):
                self.fields["precio_sugerido_venta"].initial = getattr(
                    self.instance, "precio_sugerido_venta", None
                )

        # Solo estados válidos en Alta/Edición
        allowed = {InventarioItem.Estado.EN_USO, InventarioItem.Estado.ALMACEN}
        self.fields["estado"].choices = [
            (k, v) for (k, v) in self.fields["estado"].choices if k in allowed
        ]

        # Default visual (por si llega vacío)
        self.fields["estado"].required = False

    def clean(self):
        cleaned = super().clean()

        # Blindaje: aquí NO hay bajas.
        estado = cleaned.get("estado") or InventarioItem.Estado.ALMACEN
        if estado in (InventarioItem.Estado.BAJA, InventarioItem.Estado.DESECHO):
            estado = InventarioItem.Estado.ALMACEN
        cleaned["estado"] = estado

        # Si existe el campo, muévelo al cleaned_data (por si lo agregamos dinámico)
        if "precio_sugerido_venta" in self.fields:
            cleaned["precio_sugerido_venta"] = cleaned.get("precio_sugerido_venta")

        return cleaned

    def save(self, commit=True):
        obj = super().save(commit=False)

        # Guarda el precio_sugerido_venta si el modelo lo tiene
        if "precio_sugerido_venta" in self.cleaned_data and _model_has_field(
            InventarioItem, "precio_sugerido_venta"
        ):
            setattr(obj, "precio_sugerido_venta", self.cleaned_data.get("precio_sugerido_venta"))

        if commit:
            obj.save()
            self.save_m2m()
        return obj


class InventarioBajaForm(BootstrapModelForm):
    """
    Baja/Desecho: aquí sí pedimos fecha_baja y motivo_baja.
    """

    class Meta:
        model = InventarioItem
        fields = ["estado", "fecha_baja", "motivo_baja", "observaciones"]
        widgets = {"fecha_baja": forms.DateInput(attrs={"type": "date"})}

    def clean(self):
        cleaned = super().clean()
        estado = cleaned.get("estado")

        if estado not in (InventarioItem.Estado.BAJA, InventarioItem.Estado.DESECHO):
            self.add_error("estado", "Aquí solo puedes marcar BAJA o DESECHO.")

        # Si es baja/desecho, exige fecha y motivo (para que el form lo muestre bonito)
        if estado in (InventarioItem.Estado.BAJA, InventarioItem.Estado.DESECHO):
            if not cleaned.get("fecha_baja"):
                self.add_error("fecha_baja", "Requerido cuando el equipo está dado de baja.")
            if not cleaned.get("motivo_baja"):
                self.add_error("motivo_baja", "Requerido cuando el equipo está dado de baja.")

        return cleaned
