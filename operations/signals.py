from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trip

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