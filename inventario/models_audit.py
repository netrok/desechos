from django.conf import settings
from django.db import models

class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATE = "CREATE", "Create"
        UPDATE = "UPDATE", "Update"
        BAJA   = "BAJA",   "Baja"
        DELETE = "DELETE", "Delete"

    action = models.CharField(max_length=10, choices=Action.choices)
    model = models.CharField(max_length=100)
    object_id = models.CharField(max_length=64)

    # snapshots (JSON)
    before = models.JSONField(null=True, blank=True)
    after  = models.JSONField(null=True, blank=True)

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    ip = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.created_at:%Y-%m-%d %H:%M} {self.action} {self.model}#{self.object_id}"

def get_client_ip(request):
    xff = request.META.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")
