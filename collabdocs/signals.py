
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import AuditLog, Document


@receiver(post_save, sender=Document)
def log_document_changes(sender, instance, created, **kwargs):
    action = "created" if created else "updated"

    AuditLog.objects.create(
        actor=instance.created_by,
        action=action,
        model_name="Document",
        object_id=str(instance.id),
    )
