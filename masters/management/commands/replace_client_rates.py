"""Replace a client's wrong rates with the rates in a workbook.

    python manage.py replace_client_rates "RED BULL" Redbull.xlsx                 # preview
    python manage.py replace_client_rates "RED BULL" Redbull.xlsx --apply         # do it

Workbook columns: Route, Fuel Product, Vehicle Type, Weight (Tons), Eff. Date,
Current Fuel Price, Current Rate, Effective %, Updated Fuel Price (Client Name is ignored).

Removed first (the old, wrong ones): every rate of the client on a route / vehicle / weight that is
in the workbook, plus the imported-looking fixed rates (FIXED, fuel 0, no sub-category). Rates on other
routes are kept and listed. Then the workbook's rows are added as fuel-linked rates and the
client's trips on those routes are re-priced. All in one transaction.
"""
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from masters.management.commands.move_client_rates import _client
from masters.models import ClientRate, FuelProduct, Route, VehicleType

CENT = Decimal("0.01")


def _dec(v, label, row):
    try:
        return Decimal(str(v)).quantize(CENT, rounding=ROUND_HALF_UP)
    except Exception:
        raise CommandError(f"Row {row}: {label} is not a number: {v!r}")


class Command(BaseCommand):
    help = "Delete a client's old rates and load the workbook's rates instead (preview unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("client")
        parser.add_argument("file")
        parser.add_argument("--vehicle-type-suffix", choices=("DRY", "REEFER"), default="DRY")
        parser.add_argument("--apply", action="store_true")

    def handle(self, *args, **options):
        client = _client(options["client"])
        path = Path(options["file"])
        if not path.is_absolute():
            path = Path(settings.BASE_DIR) / path
        if not path.is_file():
            raise CommandError(f"Workbook not found: {path}")
        sheet = load_workbook(path, read_only=True, data_only=True).active
        rows = sheet.iter_rows(values_only=True)
        head = {" ".join(str(h or "").lower().split()): i for i, h in enumerate(next(rows))}
        need = ["route", "fuel product", "vehicle type", "weight (tons)", "eff. date",
                "current fuel price", "current rate", "effective %", "updated fuel price"]
        miss = [n for n in need if n not in head]
        if miss:
            raise CommandError("Missing columns: " + ", ".join(miss))

        new, keys, problems = [], set(), []
        for n, r in enumerate(rows, start=2):
            if not r or not any(v is not None for v in r):
                continue
            g = lambda k: r[head[k]]
            code = str(g("route") or "").strip().upper()
            vname = str(g("vehicle type") or "").strip().upper()
            if " DRY" not in vname and " REEFER" not in vname:
                vname = f"{vname} {options['vehicle_type_suffix']}"
            route = Route.objects.filter(route_code__iexact=code).first()
            vt = VehicleType.objects.filter(name__iexact=vname).first()
            fp = FuelProduct.objects.filter(name__iexact=str(g("fuel product") or "").strip()).first()
            if not (route and vt and fp):
                problems.append(f"Row {n}: {code} / {vname} / {g('fuel product')} - "
                                f"{'route ' if not route else ''}{'vehicle ' if not vt else ''}{'fuel product ' if not fp else ''}not found")
                continue
            eff = g("eff. date")
            eff = eff.date() if isinstance(eff, datetime) else eff if isinstance(eff, date) else date.fromisoformat(str(eff)[:10])
            weight = _dec(g("weight (tons)"), "weight", n)
            if (route.id, vt.id, weight) in keys:
                problems.append(f"Row {n}: duplicate {code} / {vname} / {weight} t - skipped")
                continue
            keys.add((route.id, vt.id, weight))
            new.append(dict(route=route, vehicle_type=vt, weight_tons=weight, fuel_product=fp, effective_date=eff,
                            current_fuel_price=_dec(g("current fuel price"), "current fuel price", n),
                            current_rate=_dec(g("current rate"), "current rate", n),
                            effective_percent=_dec(g("effective %"), "effective %", n),
                            updated_fuel_price=_dec(g("updated fuel price"), "updated fuel price", n)))

        existing = list(ClientRate.objects.filter(client=client))
        old, kept = [], []
        for e in existing:
            imported = (e.rate_type == "FIXED" and not e.current_fuel_price and not e.updated_fuel_price
                        and e.sub_category_id is None)
            (old if imported or (e.route_id, e.vehicle_type_id, e.weight_tons) in keys else kept).append(e)

        self.stdout.write(f"Client: {client.name} - {len(existing)} rate(s) now")
        self.stdout.write(f"  to DELETE (old): {len(old)}   kept (other routes): {len(kept)}   to ADD: {len(new)}")
        for k in kept:
            self.stdout.write(f"  KEEP {k.route.route_code} {k.vehicle_type} {k.weight_tons} t {k.effective_date}")
        for p in problems:
            self.stderr.write(self.style.WARNING(p))
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Preview only. Add --apply to replace."))
            return
        if problems:
            raise CommandError("Fix the problems above first - nothing was changed.")

        from operations.models import refresh_trip_freight
        with transaction.atomic():
            for e in old:
                e.delete()
            for d in new:
                ClientRate(client=client, rate_type="AUTO", **d).save()
            repriced = 0
            for rid, vid, w in keys:
                repriced += refresh_trip_freight(client.id, rid, vid, w) or 0
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {len(old)} old rate(s), added {len(new)} for {client.name}; {repriced} trip(s) re-priced."))
