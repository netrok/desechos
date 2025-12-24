from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils.http import url_has_allowed_host_and_scheme


def _safe_next_url(request, default="/inventario/") -> str:
    """
    Evita open-redirect: solo permite next dentro del mismo host.
    """
    next_url = request.GET.get("next") or request.POST.get("next") or default
    if url_has_allowed_host_and_scheme(
        url=next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default


@require_http_methods(["GET", "POST"])
def login_view(request):
    # Si el usuario ya está autenticado, redirige directamente a la página principal
    if request.user.is_authenticated:
        return redirect("/inventario/")  # Redirige a inventario

    next_url = _safe_next_url(request, default="/inventario/")

    if request.method == "POST":
        username = (request.POST.get("username") or "").strip()
        password = request.POST.get("password") or ""

        # Verificación de credenciales
        if not username or not password:
            messages.error(request, "Ingresa usuario y contraseña.")
            return render(request, "core/login.html", {"next": next_url})

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Usuario o contraseña incorrectos.")
        elif not user.is_active:
            messages.error(request, "Usuario inactivo.")
        elif not user.is_staff:
            messages.error(request, "No tienes acceso a la UI interna.")
        else:
            login(request, user)
            return HttpResponseRedirect(next_url)  # Redirige a la página deseada

    return render(request, "core/login.html", {"next": next_url})


@require_http_methods(["POST"])
def logout_view(request):
    """
    Función de logout que cierra la sesión del usuario y redirige al login.
    """
    logout(request)
    messages.info(request, "Sesión cerrada.")  # Mensaje de logout exitoso
    return redirect("/login/")  # Redirige a la página de login después de cerrar sesión


# Vista para el health check, que responde con un OK
from django.http import HttpResponse

def health(request):
    """Vista para el health check"""
    return HttpResponse("OK", status=200)
