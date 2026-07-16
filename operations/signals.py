from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Trip  # Ensure Trip and Vehicle are in the same models.py

@receiver(post_save, sender=Trip)
def update_vehicle_location(sender, instance, created, **kwargs):
    """
    Jab bhi nayi Trip create hogi, ye function gari ki 
    location ko destination city par update kar dega.
    """
    if created and instance.vehicle:
        vehicle = instance.vehicle
        
        # Scenario 1: Agar Trip model mein 'route' field hai (Recommended)
        if hasattr(instance, 'route') and instance.route:
            # Route model se destination city ka naam nikalna
            vehicle.current_location = instance.route.destination.name
            vehicle.save()
            
        # Scenario 2: Agar Trip model mein direct 'destination' field hai
        elif hasattr(instance, 'destination') and instance.destination:
            vehicle.current_location = instance.destination.name
            vehicle.save()
            
        # Scenario 3: Agar field ka naam 'destination_city' hai
        elif hasattr(instance, 'destination_city') and instance.destination_city:
            vehicle.current_location = instance.destination_city.name
            vehicle.save()