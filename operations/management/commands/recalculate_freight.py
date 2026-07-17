from django.core.management.base import BaseCommand

from operations.models import Trip


class Command(BaseCommand):
    help = (
        "One-time fix: recalculates Freight = Rate + Detention on every existing "
        "trip, since older trips were saved under the previous formula. Safe to re-run."
    )

    def handle(self, *args, **options):
        updated = 0
        for trip in Trip.objects.all():
            new_freight = trip.rate + trip.detention
            if trip.freight != new_freight:
                trip.freight = new_freight
                trip.save(update_fields=["freight"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Recalculated freight for {updated} trip(s) out of {Trip.objects.count()} total."
        ))
