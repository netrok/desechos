from django.core.management.base import BaseCommand

from inventario.models import Categoria, Ubicacion, MotivoBaja


class Command(BaseCommand):
    help = "Siembra catálogos base (categorías, ubicaciones, motivos de baja)."

    def handle(self, *args, **options):
        categorias = [
            "CPU/PC",
            "Laptop",
            "Monitor",
            "Impresora",
            "No-break/UPS",
            "Switch/Router",
            "DVR/CCTV",
            "Teléfono/Tablet",
            "Accesorios",
            "Otros",
        ]

        ubicaciones = [
            "Almacén",
            "Sistemas",
            "Oficina",
            "Sucursal 01",
            "Sucursal 02",
        ]

        motivos = [
            "Obsoleto",
            "Daño irreparable",
            "Robo/Extravío",
            "Donación",
            "Venta",
            "Reemplazo",
        ]

        c_created = 0
        for nombre in categorias:
            _, created = Categoria.objects.get_or_create(nombre=nombre)
            c_created += int(created)

        u_created = 0
        for nombre in ubicaciones:
            _, created = Ubicacion.objects.get_or_create(nombre=nombre)
            u_created += int(created)

        m_created = 0
        for nombre in motivos:
            _, created = MotivoBaja.objects.get_or_create(nombre=nombre)
            m_created += int(created)

        self.stdout.write(self.style.SUCCESS("Seed listo ✅"))
        self.stdout.write(f"Categorías nuevas: {c_created}")
        self.stdout.write(f"Ubicaciones nuevas: {u_created}")
        self.stdout.write(f"Motivos nuevos: {m_created}")
