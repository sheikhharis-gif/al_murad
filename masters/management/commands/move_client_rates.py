"""Move rates imported onto the wrong client to the right one.

    python manage.py move_client_rates "NATIONAL FOODS" "RED BULL"                 # list what's there
    python manage.py move_client_rates "NATIONAL FOODS" "RED BULL" --effective-date 2026-10-01           # preview
    python manage.py move_client_rates "NATIONAL FOODS" "RED BULL" --effective-date 2026-10-01 --apply   # do it

Only rates that look like an `import_client_rates` import are touched: FIXED,
fuel price 0, no sub-category, on the given effective date. They are moved
(same values) - not copied - and the trips of both clients on those routes are
re-priced. If the target already has the same route / vehicle / tonnage / date,
that row is left on the source and listed, so nothing is doubled.
"""
from collections import Counter
from datetime import date

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from masters.models import Client, ClientRate


def _client(name):
    exact = Client.objects.filter(name__iexact=name.strip())
    matches = list(exact) or list(Client.objects.filter(name__icontains=name.strip()))
    if len(matches) != 1:
        found = ", ".join(c.name for c in matches) or "none"
        raise CommandError(f"Client '{name}': expected exactly one match, found {found}. Use the full name.")
    return matches[0]


class Command(BaseCommand):
    help = "Move imported fixed rates from one client to another (preview unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("from_client")
        parser.add_argument("to_client")
        parser.add_argument("--effective-date", help="YYYY-MM-DD of the wrong import.")
        parser.add_argument("--apply", action="store_true", help="Save. Without it, preview only.")

    def handle(self, *args, **options):
        src, dst = _client(options["from_client"]), _client(options["to_client"])
        if src.id == dst.id:
            raise CommandError("From and To are the same client.")
        imported = ClientRate.objects.filter(client=src, rate_type="FIXED", current_fuel_price=0,
                                             updated_fuel_price=0, sub_category__isnull=True)
        self.stdout.write(f"From: {src.name} (all rates: {src.rates.count()})  ->  To: {dst.name} (all rates: {dst.rates.count()})")

        if not options["effective_date"]:
            groups = Counter(imported.values_list("effective_date", flat=True))
            if not groups:
                self.stdout.write("No imported-looking fixed rates on the source client.")
                return
            self.stdout.write("Imported-looking fixed rates on the source, by effective date:")
            for d, n in sorted(groups.items()):
                self.stdout.write(f"   {d}  ->  {n} rate(s)")
            self.stdout.write(self.style.WARNING("Run again with --effective-date YYYY-MM-DD to preview the move."))
            return

        try:
            eff = date.fromisoformat(options["effective_date"])
        except ValueError:
            raise CommandError("Effective date must be YYYY-MM-DD.")
        rows = list(imported.filter(effective_date=eff).select_related("route", "vehicle_type").order_by("route__route_code", "id"))
        move, clash = [], []
        for r in rows:
            exists = ClientRate.objects.filter(client=dst, route_id=r.route_id, vehicle_type_id=r.vehicle_type_id,
                                               weight_tons=r.weight_tons, effective_date=eff,
                                               sub_category__isnull=True).exists()
            (clash if exists else move).append(r)
        for r in move:
            self.stdout.write(f"   MOVE  {r.route.route_code:<12} {str(r.vehicle_type or '--'):<14} {r.weight_tons} t  {r.current_rate:>12,}")
        for r in clash:
            self.stdout.write(self.style.WARNING(
                f"   SKIP  {r.route.route_code} / {r.vehicle_type} / {r.weight_tons} t - {dst.name} already has it on {eff}"))
        self.stdout.write(f"{len(move)} to move, {len(clash)} skipped.")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Preview only. Add --apply to move them."))
            return

        from operations.models import refresh_trip_freight
        keys = {(r.route_id, r.vehicle_type_id, r.weight_tons) for r in move}
        with transaction.atomic():
            ClientRate.objects.filter(id__in=[r.id for r in move]).update(client=dst)
            repriced = 0
            for route_id, vt_id, w in keys:
                for client_id in (src.id, dst.id):
                    repriced += refresh_trip_freight(client_id, route_id, vt_id, w) or 0
        self.stdout.write(self.style.SUCCESS(
            f"Moved {len(move)} rate(s) from {src.name} to {dst.name}; {repriced} trip(s) re-priced."))
