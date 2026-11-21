from collections import Counter

from django.core.management.base import BaseCommand
from django.db import transaction

from operations.models import Trip, matching_trip_cost


class Command(BaseCommand):
    help = ("Re-work every trip's freight from the Client Rates (what saving the trip does). Preview by default; "
            "--apply writes the new freight. Trips on a live invoice are never touched. "
            "Also lists the trips that have NO matching rate (client + route + vehicle type + tonnage).")

    def add_arguments(self, parser):
        parser.add_argument("--client", help="Only this client (part of the name)")
        parser.add_argument("--apply", action="store_true", help="Save the changes (otherwise just a preview)")

    def handle(self, *args, **opts):
        trips = Trip.objects.filter(empty_trip=False).select_related("client", "route", "vehicle_type")
        if opts["client"]:
            trips = trips.filter(client__name__icontains=opts["client"])
        invoiced = Trip.invoiced_ids()
        changes, no_rate, locked = [], Counter(), 0
        per_client = Counter()
        for t in trips.order_by("client__name", "trip_date", "id"):
            rate = matching_trip_cost(t.client_id, t.route_id, *t.rate_key(), t.trip_date,
                                      sub_category_id=t.sub_category_id)
            if rate is None:
                no_rate[(t.client.name if t.client_id else "-", t.route.route_code if t.route_id else "-",
                         str(t.vehicle_type or "-"), str(t.weight))] += 1
            new = (rate or 0) + (t.additional_charges or 0) + (t.stopover_charges or 0)
            if new == t.freight:
                continue
            if t.pk in invoiced:
                locked += 1
                continue
            changes.append((t, new))
            per_client[t.client.name if t.client_id else "-"] += 1

        self.stdout.write(f"Trips whose freight would change: {len(changes)}  (on a live invoice, left alone: {locked})")
        for name, n in per_client.most_common():
            self.stdout.write(f"   {name}: {n}")
        for t, new in changes[:15]:
            self.stdout.write(f"   trip {t.trip_no} {t.client} {t.route} {t.trip_date}: {t.freight} -> {new}")
        if no_rate:
            self.stdout.write(self.style.WARNING("No Client Rate matches these (client, route, vehicle type, tons) - add the rate:"))
            for (c, r, v, w), n in no_rate.most_common(30):
                self.stdout.write(f"   {c} | {r} | {v} | {w} T  ({n} trips)")
        if not opts["apply"]:
            self.stdout.write("Preview only - add --apply to save.")
            return
        with transaction.atomic():
            for t, new in changes:
                Trip.objects.filter(pk=t.pk).update(freight=new)
        self.stdout.write(self.style.SUCCESS(f"Updated {len(changes)} trips."))
