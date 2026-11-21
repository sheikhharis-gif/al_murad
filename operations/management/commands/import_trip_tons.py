from decimal import Decimal, InvalidOperation

import openpyxl
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from masters.models import ClientRate
from operations.models import Trip, matching_trip_cost


def _dec(value):
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = ("Trip Details workbook (sheets KHI / LHE ...) -> the trips named in its 'trip #' column get the tons "
            "from the sheet as their Weight, and a Rate Category (the rate the system should price them by). "
            "A trip that is already priced by its own vehicle type + tons keeps exactly that rate; any other "
            "trip gets the rate of its route whose price matches the sheet's Freight. Preview by default; "
            "--apply saves. Trips on a live invoice are never touched.")

    def add_arguments(self, parser):
        parser.add_argument("file")
        parser.add_argument("--client", default="red bull", help="Only trips of this client (part of the name)")
        parser.add_argument("--tolerance", type=float, default=0.5, help="Freight match tolerance in %% (default 0.5)")
        parser.add_argument("--apply", action="store_true")

    def read_rows(self, path):
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except Exception as exc:
            raise CommandError(f"Cannot open {path}: {exc}")
        rows = []
        for ws in wb:
            header, cols = None, {}
            for r in ws.iter_rows(values_only=True):
                labels = [str(c).strip().lower() if c is not None else "" for c in r]
                if "trip #" in labels and "weight (tons)" in labels:
                    header = True
                    cols = {"trip": labels.index("trip #"), "tons": labels.index("weight (tons)"),
                            "freight": labels.index("freight")}
                    continue
                if not header:
                    continue
                trip_no, tons, freight = r[cols["trip"]], r[cols["tons"]], r[cols["freight"]]
                if trip_no in (None, "") or tons in (None, ""):
                    continue
                try:
                    trip_no = f"{int(trip_no):06d}"
                except (TypeError, ValueError):
                    continue
                rows.append((ws.title, trip_no, _dec(tons), _dec(freight)))
        return rows

    def handle(self, *args, **opts):
        rows = self.read_rows(opts["file"])
        if not rows:
            raise CommandError("No trip rows found (needs 'trip #' and 'Weight (Tons)' columns).")
        tol = Decimal(str(opts["tolerance"])) / 100
        invoiced = Trip.invoiced_ids()
        plan, problems = [], []
        for sheet, trip_no, tons, freight in rows:
            trip = (Trip.objects.filter(trip_no=trip_no, client__name__icontains=opts["client"])
                    .select_related("client", "route", "vehicle_type").first())
            if not trip:
                problems.append(f"[{sheet}] trip {trip_no}: not found for client '{opts['client']}'")
                continue
            if trip.pk in invoiced:
                problems.append(f"[{sheet}] trip {trip_no}: on a live invoice - left alone")
                continue
            how, cat = "", None
            if trip.rate_vehicle_type_id and trip.rate_weight is not None:
                cat, how = (trip.rate_vehicle_type_id, trip.rate_weight), "already has a category"
            elif trip.vehicle_type_id and trip.weight is not None and matching_trip_cost(
                    trip.client_id, trip.route_id, trip.vehicle_type_id, trip.weight, trip.trip_date,
                    sub_category_id=trip.sub_category_id) is not None:
                cat, how = (trip.vehicle_type_id, trip.weight), "its own type + tons"
            elif freight:
                combos = {(r.vehicle_type_id, r.weight_tons) for r in ClientRate.objects.filter(
                    client_id=trip.client_id, route_id=trip.route_id, weight_tons__isnull=False,
                    vehicle_type__isnull=False, sub_category_id=trip.sub_category_id)}
                hits = []
                for vt, w in combos:
                    cost = matching_trip_cost(trip.client_id, trip.route_id, vt, w, trip.trip_date,
                                              sub_category_id=trip.sub_category_id)
                    if cost and abs(cost - freight) <= freight * tol:
                        hits.append((abs(cost - freight), vt, w))
                if hits:
                    hits.sort(key=lambda h: (h[0], abs(h[2] - tons)))
                    cat, how = (hits[0][1], hits[0][2]), "rate matching the sheet's freight" + (
                        f" ({len(hits)} equal-priced rates - closest tons taken)" if len(hits) > 1 else "")
            plan.append((trip, tons, freight, cat, how))
            if not cat:
                problems.append(f"[{sheet}] trip {trip_no} {trip.route} {trip.vehicle_type}: no rate matches "
                                f"freight {freight} - pick its Rate Category by hand")

        self.stdout.write(f"{len(rows)} rows in the file, {len(plan)} trips found.")
        for trip, tons, freight, cat, how in plan:
            label = "-"
            if cat:
                from masters.models import VehicleType
                label = f"{cat[1]} T / {VehicleType.objects.get(pk=cat[0]).name}"
            self.stdout.write(f"   trip {trip.trip_no} {trip.route} | {trip.vehicle_type} | weight {trip.weight} -> {tons} | "
                              f"category {label} ({how or 'none'})")
        if problems:
            self.stdout.write(self.style.WARNING("Check these:"))
            for p in problems:
                self.stdout.write("   " + p)
        if not opts["apply"]:
            self.stdout.write("Preview only - add --apply to save.")
            return
        with transaction.atomic():
            for trip, tons, freight, cat, how in plan:
                trip.weight = tons
                if cat:
                    trip.rate_vehicle_type_id, trip.rate_weight = cat
                new = trip.compute_freight()
                Trip.objects.filter(pk=trip.pk).update(
                    weight=tons, rate_vehicle_type=trip.rate_vehicle_type_id, rate_weight=trip.rate_weight,
                    freight=new)
        self.stdout.write(self.style.SUCCESS(f"Updated {len(plan)} trips."))
