import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from masters.models import Route, VehicleType, FuelProduct, Client, ClientRate
from .import_five_star_rates import CLIENT_NAME, ROWS, VEHICLE_SIZE_MAP

# Same date-wise diesel price series applied to every route/vehicle/weight
# combo Five Star bills - copied verbatim from the client's updated sheet
# (the "Effective date"/"Fuel Price" column pairs after the Aug 1 baseline,
# identical across all 58 rows). Each entry only carries its own
# updated_fuel_price/effective_percent - ClientRate.save() auto-chains
# current_fuel_price/current_rate from whichever entry was saved right
# before it for that same route+product+vehicle type+weight, as long as
# entries are created in date order (enforced by AUG_UPDATES' order below).
AUG_UPDATES = [
    (datetime.date(2026, 8, 4), "389.93"),
    (datetime.date(2026, 8, 5), "385.86"),
    (datetime.date(2026, 8, 6), "383.86"),
    (datetime.date(2026, 8, 7), "382.36"),
    (datetime.date(2026, 8, 8), "380.86"),
    (datetime.date(2026, 8, 12), "382.25"),
    (datetime.date(2026, 8, 13), "382.79"),
    (datetime.date(2026, 8, 14), "383.95"),
    (datetime.date(2026, 8, 18), "390.42"),
    (datetime.date(2026, 8, 19), "395.69"),
    (datetime.date(2026, 8, 20), "363.06"),
    (datetime.date(2026, 8, 21), "364.70"),
    (datetime.date(2026, 8, 22), "368.29"),
    (datetime.date(2026, 8, 25), "370.69"),
    (datetime.date(2026, 8, 26), "371.80"),
    (datetime.date(2026, 8, 28), "371.61"),
    (datetime.date(2026, 8, 29), "371.44"),
]

EFFECTIVE_PERCENT = Decimal("50")


class Command(BaseCommand):
    help = f"Apply Five Star 3PL's August date-wise diesel price updates for '{CLIENT_NAME}'."

    def handle(self, *args, **options):
        client = Client.objects.filter(name__iexact=CLIENT_NAME).first()
        if not client:
            self.stderr.write(self.style.ERROR(f"Client '{CLIENT_NAME}' not found."))
            return

        diesel_product = FuelProduct.objects.filter(name="HI-CETANE DIESEL EURO5").first()
        if not diesel_product:
            self.stderr.write(self.style.ERROR(
                "FuelProduct 'HI-CETANE DIESEL EURO5' not found - run cleanup_fuel_products first."
            ))
            return

        created, updated, skipped_combos = 0, 0, 0
        for route_code, vtype_raw, weight, _base_rate in ROWS:
            route = Route.objects.filter(route_code=route_code).first()
            if not route:
                self.stderr.write(self.style.WARNING(f"Route '{route_code}' not found, skipped."))
                skipped_combos += 1
                continue

            vtype_key = "".join(vtype_raw.upper().split())
            vehicle_type = VehicleType.objects.filter(name=VEHICLE_SIZE_MAP[vtype_key]).first()
            if not vehicle_type:
                self.stderr.write(self.style.WARNING(f"VehicleType '{VEHICLE_SIZE_MAP[vtype_key]}' not found, skipped."))
                skipped_combos += 1
                continue

            weight_dec = Decimal(str(weight)).quantize(Decimal("0.01"))

            for eff_date, price in AUG_UPDATES:
                obj, was_created = ClientRate.objects.update_or_create(
                    client=client,
                    route=route,
                    fuel_product=diesel_product,
                    vehicle_type=vehicle_type,
                    weight_tons=weight_dec,
                    effective_date=eff_date,
                    defaults={
                        "effective_percent": EFFECTIVE_PERCENT,
                        "updated_fuel_price": Decimal(price),
                    },
                )
                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created}, updated {updated} row(s), skipped {skipped_combos} route/vehicle combo(s)."
        ))
