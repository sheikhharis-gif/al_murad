from django.core.management.base import BaseCommand
from django.db import transaction

from operations.models import Trip, matching_trip_cost


class Command(BaseCommand):
    help = ("For a client's existing trips: the vehicle type + tons a trip is priced by become its Rate Category, "
            "and the trip's Weight (Tons) box is cleared (typed by hand from now on). Freight does not change. "
            "Trips that have no matching rate keep their weight. Preview by default; --apply saves.")

    def add_arguments(self, parser):
        parser.add_argument("client", help="Client name (part of it), e.g. 'red bull'")
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **opts):
        trips = (Trip.objects.filter(client__name__icontains=opts["client"], empty_trip=False,
                                     rate_vehicle_type__isnull=True, weight__isnull=False, vehicle_type__isnull=False)
                 .select_related("client", "route", "vehicle_type").order_by("id"))
        invoiced = Trip.invoiced_ids()
        move, skipped, locked = [], [], 0
        for t in trips:
            if matching_trip_cost(t.client_id, t.route_id, t.vehicle_type_id, t.weight, t.trip_date,
                                  sub_category_id=t.sub_category_id) is None:
                skipped.append(t)
            elif t.pk in invoiced:
                locked += 1
            else:
                move.append(t)
        names = sorted({t.client.name for t in list(move) + skipped})
        self.stdout.write(f"Client(s): {', '.join(names) or '(none found)'}")
        self.stdout.write(f"Trips to move into Rate Category (weight box cleared): {len(move)}")
        self.stdout.write(f"Left alone - on a live invoice: {locked}")
        self.stdout.write(f"Left alone - no matching rate (they keep their weight): {len(skipped)}")
        for t in skipped[:30]:
            self.stdout.write(f"   trip {t.trip_no}: {t.route} | {t.vehicle_type} | {t.weight} T")
        for t in move[:10]:
            self.stdout.write(f"   trip {t.trip_no}: {t.route} | {t.vehicle_type} | {t.weight} T -> category")
        if not opts["apply"]:
            self.stdout.write("Preview only - add --apply to save.")
            return
        with transaction.atomic():
            for t in move:
                Trip.objects.filter(pk=t.pk).update(rate_vehicle_type=t.vehicle_type_id, rate_weight=t.weight, weight=None)
        self.stdout.write(self.style.SUCCESS(f"Moved {len(move)} trips."))
