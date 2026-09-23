from django.core.management.base import BaseCommand

from operations.models import Trip


class Command(BaseCommand):
    help = (
        "Re-prices every trip from the current Client Rates (latest rate for the "
        "trip's client + route + vehicle type + tonnage, plus additional charges). "
        "Only the freight column is changed. Safe to re-run."
    )

    def handle(self, *args, **options):
        updated = 0
        trips = Trip.objects.all()
        for trip in trips:
            freight = trip.compute_freight()
            if trip.freight != freight:
                Trip.objects.filter(pk=trip.pk).update(freight=freight)
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Recalculated freight for {updated} trip(s) out of {trips.count()} total."
        ))
