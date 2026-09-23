from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from masters.models import ClientRate
from .models import Trip, refresh_trip_freight


def _rate_key(rate):
    return (rate.client_id, rate.route_id, rate.vehicle_type_id, rate.weight_tons)


@receiver(pre_save, sender=ClientRate)
def _stash_old_rate_key(sender, instance, **kwargs):
    """Editing a rate can move it to another route/type/tonnage - remember the
    old one so trips priced off it are refreshed too."""
    old = ClientRate.objects.filter(pk=instance.pk).first() if instance.pk else None
    instance._old_rate_key = _rate_key(old) if old else None


@receiver(post_save, sender=ClientRate)
def _reprice_trips_on_rate_save(sender, instance, **kwargs):
    old_key = getattr(instance, "_old_rate_key", None)
    if old_key and old_key != _rate_key(instance):
        refresh_trip_freight(*old_key)
    refresh_trip_freight(*_rate_key(instance))


@receiver(post_delete, sender=ClientRate)
def _reprice_trips_on_rate_delete(sender, instance, **kwargs):
    refresh_trip_freight(*_rate_key(instance))


@receiver(post_save, sender=Trip)
def update_vehicle_location(sender, instance, created, **kwargs):
    """
    Vehicle ki current location sirf tab destination par jump karti hai jab
    trip mein actual arrival record ho chuki ho (arrived_at set), na ke sirf
    trip row create/save hone par - warna reached_at (origin pe pahunchna/
    loading ke liye) bharne se hi location samay se pehle destination dikha
    deti thi. Isi wajah se yeh har save (create aur edit dono) par chalta
    hai, kyunke arrived_at aam tor par trip create hone ke baad, ek baad ki
    edit mein bhara jata hai.
    """
    if not instance.arrived_at or not instance.vehicle_id or not instance.route_id:
        return

    vehicle = instance.vehicle
    destination = instance.route.destination
    if vehicle.current_location_id != destination.pk:
        vehicle.current_location = destination
        vehicle.save(update_fields=["current_location"])