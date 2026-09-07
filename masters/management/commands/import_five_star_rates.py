import datetime
from decimal import Decimal

from django.core.management.base import BaseCommand

from masters.models import City, Route, Client, FuelProduct, VehicleType, ClientRate

CLIENT_NAME = "Five Star 3PL SERVICES"

# Every row shares the same fuel product, effective date, current fuel
# price, effective %, and updated fuel price - only the route, vehicle
# size/weight, and current rate vary. Values copied verbatim from
# "FIVE star rate file aug (upload).xlsx" (58 rows).
EFFECTIVE_DATE = datetime.date(2026, 8, 1)
CURRENT_FUEL_PRICE = Decimal("393.04")
EFFECTIVE_PERCENT = Decimal("50")
UPDATED_FUEL_PRICE = Decimal("392.38")

# (route_code, vehicle size as written in the sheet, weight in tons, current rate)
ROWS = [
    ("KHI-GUJ", "20FT", 8, 189714.6853865805),
    ("KHI-ISB", "20FT", 8, 221869.71680803486),
    ("KHI-LHE", "20FT", 8, 183283.67910228964),
    ("KHI-MUX", "20FT", 8, 163990.660249417),
    ("KHI-PEW", "20FT", 8, 247593.74194519833),
    ("KHI-SWL", "20FT", 8, 183283.67910228964),
    ("KHI-SKT", "20FT", 8, 221869.71680803486),
    ("KHI-QTA", "20FT", 8, 163990.660249417),
    ("KHI-KHI", "20FT", 8, 25080.924508734366),
    ("KHI-SKZ", "20FT", 8, 106111.60369079925),
    ("KHI-LRK", "20FT", 8, 106111.60369079925),
    ("KHI-SGD", "20FT", 8, 196145.6916708714),
    ("KHI-BWP", "20FT", 8, 163990.660249417),
    ("KHI-HYD", "20FT", 8, 54663.553416472365),
    ("KHI-FSD", "40 FT", 16, 321550.3142145432),
    ("KHI-GUJ", "40 FT", 16, 353705.3456359976),
    ("KHI-ISB", "40 FT", 16, 405153.39591032447),
    ("KHI-LHE", "40 FT", 16, 327981.320498834),
    ("KHI-MUX", "40 FT", 16, 231516.22623447108),
    ("KHI-PEW", "40 FT", 16, 405153.39591032447),
    ("KHI-SWL", "40 FT", 16, 317691.71044396877),
    ("KHI-SKT", "40 FT", 16, 495187.48389039666),
    ("KHI-QTA", "40 FT", 16, 244378.23880305287),
    ("KHI-KHI", "40 FT", 16, 45017.04399003608),
    ("KHI-SKZ", "40 FT", 16, 154344.15082298077),
    ("KHI-LRK", "40 FT", 16, 173637.1696758533),
    ("KHI-SGD", "40 FT", 16, 353705.3456359976),
    ("KHI-BWP", "40 FT", 16, 237947.232518762),
    ("KHI-HYD", "40 FT", 16, 93249.59112221753),
    ("KHI-GUJ", "50FT", 20, 366567.3582045793),
    ("KHI-ISB", "50FT", 20, 421874.0122494807),
    ("KHI-LHE", "50FT", 20, 353705.3456359976),
    ("KHI-MUX", "50FT", 20, 257240.25137163454),
    ("KHI-PEW", "50FT", 20, 437308.4273317789),
    ("KHI-SWL", "50FT", 20, 340843.3330674158),
    ("KHI-SKT", "50FT", 20, 385860.37705745175),
    ("KHI-QTA", "50FT", 20, 272674.66645393264),
    ("KHI-KHI", "50FT", 20, 77172.07541149038),
    ("KHI-SKZ", "50FT", 20, 186499.18224443507),
    ("KHI-LRK", "50FT", 20, 205792.20109730764),
    ("KHI-SGD", "50FT", 20, 366567.3582045793),
    ("KHI-BWP", "50FT", 20, 250809.24508734382),
    ("KHI-HYD", "50FT", 20, 102896.10054865382),
    ("KHI-FSD", "55 FT", 22, 372998.36448887014),
    ("KHI-GUJ", "55 FT", 22, 396149.9871123173),
    ("KHI-ISB", "55 FT", 22, 424446.414763197),
    ("KHI-LHE", "55 FT", 22, 372998.36448887014),
    ("KHI-MUX", "55 FT", 22, 295826.28907737974),
    ("KHI-PEW", "55 FT", 22, 450170.43990036054),
    ("KHI-SWL", "55 FT", 22, 360136.35192028864),
    ("KHI-SKT", "55 FT", 22, 418015.4084789062),
    ("KHI-QTA", "55 FT", 22, 276533.27022450714),
    ("KHI-KHI", "55 FT", 22, 102896.10054865382),
    ("KHI-SKZ", "55 FT", 22, 218654.21366588946),
    ("KHI-LRK", "55 FT", 22, 237947.232518762),
    ("KHI-SGD", "55 FT", 22, 398722.3896260336),
    ("KHI-BWP", "55 FT", 22, 289395.2827930889),
    ("KHI-HYD", "55 FT", 22, 128620.12568581727),
]

# Destination city code -> (full name, latitude, longitude, approx KM from
# Karachi by road). Coordinates/distances are best-effort placeholders where
# the real Route/City record doesn't already exist - get_or_create leaves
# any existing (real) record untouched, only filling gaps for new ones.
CITY_DATA = {
    "KHI": ("KARACHI", Decimal("24.8607"), Decimal("67.0011"), 0),
    "GUJ": ("GUJRANWALA", Decimal("32.1877"), Decimal("74.1945"), 1300),
    "ISB": ("ISLAMABAD", Decimal("33.6844"), Decimal("73.0479"), 1410),
    "LHE": ("LAHORE", Decimal("31.5497"), Decimal("74.3436"), 1225),
    "MUX": ("MULTAN", Decimal("30.1575"), Decimal("71.5249"), 950),
    "PEW": ("PESHAWAR", Decimal("34.0151"), Decimal("71.5249"), 1620),
    "SWL": ("SAHIWAL", Decimal("30.6682"), Decimal("73.1114"), 1100),
    "SKT": ("SIALKOT", Decimal("32.4945"), Decimal("74.5229"), 1370),
    "QTA": ("QUETTA", Decimal("30.1798"), Decimal("66.9750"), 700),
    "SKZ": ("SHIKARPUR", Decimal("27.9560"), Decimal("68.6382"), 500),
    "LRK": ("LARKANA", Decimal("27.5590"), Decimal("68.2120"), 470),
    "SGD": ("SARGODHA", Decimal("32.0836"), Decimal("72.6711"), 1160),
    "BWP": ("BAHAWALPUR", Decimal("29.4000"), Decimal("71.6833"), 750),
    "HYD": ("HYDERABAD", Decimal("25.3960"), Decimal("68.3578"), 165),
    "FSD": ("FAISALABAD", Decimal("31.4180"), Decimal("73.0790"), 1070),
}

# Sheet just says "20FT"/"40 FT"/"50FT"/"55 FT" with no DRY/REEFER - client
# confirmed DRY for all sizes.
VEHICLE_SIZE_MAP = {
    "20FT": "20FT DRY",
    "40FT": "40FT DRY",
    "50FT": "50FT DRY",
    "55FT": "55FT DRY",
}


def _dec(value):
    return Decimal(str(value)).quantize(Decimal("0.01"))


class Command(BaseCommand):
    help = f"Import Client Rate entries for '{CLIENT_NAME}' (data embedded from the client's rate sheet)."

    def handle(self, *args, **options):
        client = Client.objects.filter(name__iexact=CLIENT_NAME).first()
        if not client:
            self.stderr.write(self.style.ERROR(f"Client '{CLIENT_NAME}' not found - create it first."))
            return

        diesel_product, _ = FuelProduct.objects.get_or_create(name="DIESEL")

        khi_name, khi_lat, khi_lng, _ = CITY_DATA["KHI"]
        khi_city, _ = City.objects.get_or_create(
            code="KHI", defaults={"name": khi_name, "latitude": khi_lat, "longitude": khi_lng}
        )

        created, updated, skipped = 0, 0, 0
        for route_code, vtype_raw, weight, cur_rate in ROWS:
            _origin_code, dest_code = route_code.split("-", 1)
            dest_info = CITY_DATA.get(dest_code)
            if not dest_info:
                self.stderr.write(self.style.WARNING(f"Unknown destination city code '{dest_code}', skipped."))
                skipped += 1
                continue

            dest_name, dest_lat, dest_lng, dest_km = dest_info
            dest_city, _ = City.objects.get_or_create(
                code=dest_code, defaults={"name": dest_name, "latitude": dest_lat, "longitude": dest_lng}
            )
            route, _ = Route.objects.get_or_create(
                origin=khi_city, destination=dest_city, defaults={"distance_km": dest_km}
            )

            vtype_key = "".join(vtype_raw.upper().split())
            vehicle_type, _ = VehicleType.objects.get_or_create(name=VEHICLE_SIZE_MAP[vtype_key])

            obj, was_created = ClientRate.objects.update_or_create(
                client=client,
                route=route,
                fuel_product=diesel_product,
                vehicle_type=vehicle_type,
                weight_tons=_dec(weight),
                effective_date=EFFECTIVE_DATE,
                defaults={
                    "current_fuel_price": CURRENT_FUEL_PRICE,
                    "current_rate": _dec(cur_rate),
                    "effective_percent": EFFECTIVE_PERCENT,
                    "updated_fuel_price": UPDATED_FUEL_PRICE,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Done. Created {created}, updated {updated}, skipped {skipped} row(s)."
        ))
