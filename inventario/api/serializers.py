from rest_framework import serializers
from inventario.models import Categoria, Ubicacion, MotivoBaja, InventarioItem


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = "__all__"


class UbicacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ubicacion
        fields = "__all__"


class MotivoBajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MotivoBaja
        fields = "__all__"


class InventarioItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InventarioItem
        fields = "__all__"
        read_only_fields = ("codigo", "fecha_alta")
