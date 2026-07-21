from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .models import MaintenancePart, PartsInventory


@receiver(pre_save, sender=MaintenancePart)
def _stash_old_inventory_item(sender, instance, **kwargs):
    """Remember the previous linked inventory item so we can refresh it too if it changed."""
    if instance.pk:
        previous = MaintenancePart.objects.filter(pk=instance.pk).values_list("inventory_item_id", flat=True).first()
        instance._old_inventory_item_id = previous
    else:
        instance._old_inventory_item_id = None


def _refresh(part_id):
    if not part_id:
        return
    item = PartsInventory.objects.filter(pk=part_id).first()
    if item:
        item.save()


@receiver(post_save, sender=MaintenancePart)
def _refresh_inventory_on_save(sender, instance, **kwargs):
    old_id = getattr(instance, "_old_inventory_item_id", None)
    if old_id and old_id != instance.inventory_item_id:
        _refresh(old_id)
    _refresh(instance.inventory_item_id)


@receiver(post_delete, sender=MaintenancePart)
def _refresh_inventory_on_delete(sender, instance, **kwargs):
    _refresh(instance.inventory_item_id)
