from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import InventarioBajaForm, InventarioItemForm
from .models import Categoria, InventarioItem, Ubicacion

STAFF_LOGIN_URL = "/login/"  # Definir aquí solo una vez para el login


@staff_member_required(login_url=STAFF_LOGIN_URL)
def item_list(request):
    qs = InventarioItem.objects.select_related("categoria", "ubicacion", "motivo_baja").all()

    # Filtros de búsqueda
    search = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    ubicacion_id = request.GET.get("ubicacion", "").strip()
    estado = request.GET.get("estado", "").strip()
    activo = request.GET.get("activo", "").strip()

    # Aplicando filtros de búsqueda
    if search:
        qs = qs.filter(
            Q(codigo__icontains=search)
            | Q(serie__icontains=search)
            | Q(modelo__icontains=search)
            | Q(marca__icontains=search)
            | Q(etiqueta_interna__icontains=search)
            | Q(responsable__icontains=search)
        )

    if categoria_id:
        qs = qs.filter(categoria_id=categoria_id)

    if ubicacion_id:
        qs = qs.filter(ubicacion_id=ubicacion_id)

    if estado:
        qs = qs.filter(estado=estado)

    if activo in ("true", "false"):
        qs = qs.filter(activo=(activo == "true"))

    # Ordenar y paginar resultados
    qs = qs.order_by("-fecha_alta", "codigo")
    paginator = Paginator(qs, 20)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "categorias": Categoria.objects.all().order_by("nombre"),
        "ubicaciones": Ubicacion.objects.all().order_by("nombre"),
        "estados": InventarioItem.Estado.choices,
        "filters": {
            "q": search,
            "categoria": categoria_id,
            "ubicacion": ubicacion_id,
            "estado": estado,
            "activo": activo,
        },
    }
    return render(request, "inventario/item_list.html", context)


@staff_member_required(login_url=STAFF_LOGIN_URL)
def item_detail(request, pk: int):
    item = get_object_or_404(
        InventarioItem.objects.select_related("categoria", "ubicacion", "motivo_baja"),
        pk=pk,
    )
    return render(request, "inventario/item_detail.html", {"item": item})


@staff_member_required(login_url=STAFF_LOGIN_URL)
def item_create(request):
    if request.method == "POST":
        form = InventarioItemForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                obj.full_clean()
                obj.save()

                # Trae el código generado por la BD
                obj.refresh_from_db()

                messages.success(request, f"✅ Item guardado correctamente: {obj.codigo}")
                return redirect("inventario_ui:item_detail", pk=obj.pk)
            except ValidationError as e:
                # Agregar errores del modelo al form sin reventar
                form.add_error(None, e)
                messages.error(request, "❌ No se pudo guardar. Revisa los campos.")
    else:
        form = InventarioItemForm()

    return render(request, "inventario/item_form.html", {"form": form, "title": "Nuevo item"})


@staff_member_required(login_url=STAFF_LOGIN_URL)
def item_update(request, pk: int):
    item = get_object_or_404(
        InventarioItem.objects.select_related("categoria", "ubicacion", "motivo_baja"),
        pk=pk,
    )

    if request.method == "POST":
        form = InventarioItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            obj = form.save(commit=False)
            try:
                obj.full_clean()
                obj.save()
                obj.refresh_from_db()

                messages.success(request, f"✅ Cambios guardados: {obj.codigo or obj.pk}")
                return redirect("inventario_ui:item_detail", pk=obj.pk)
            except ValidationError as e:
                form.add_error(None, e)
                messages.error(request, "❌ No se pudo actualizar. Revisa los campos.")
    else:
        form = InventarioItemForm(instance=item)

    return render(
        request,
        "inventario/item_form.html",
        {"form": form, "title": f"Editar {item.codigo or item.pk}"},
    )


@staff_member_required(login_url=STAFF_LOGIN_URL)
def item_baja(request, pk: int):
    item = get_object_or_404(InventarioItem, pk=pk)

    if request.method == "POST":
        form = InventarioBajaForm(request.POST, instance=item)
        if form.is_valid():
            obj = form.save(commit=False)

            # Baja/Desecho => marcar activo False
            obj.activo = False

            # Si no mandan fecha, ponemos hoy
            if not obj.fecha_baja:
                obj.fecha_baja = timezone.localdate()

            try:
                obj.full_clean()
                obj.save()
                obj.refresh_from_db()

                messages.success(request, f"⚠️ Item marcado como baja/desecho: {obj.codigo or obj.pk}")
                return redirect("inventario_ui:item_detail", pk=obj.pk)
            except ValidationError as e:
                form.add_error(None, e)
                messages.error(request, "❌ No se pudo dar de baja. Revisa fecha/motivo.")
    else:
        form = InventarioBajaForm(
            instance=item,
            initial={"estado": InventarioItem.Estado.BAJA},
        )

    return render(request, "inventario/item_baja.html", {"form": form, "item": item})

