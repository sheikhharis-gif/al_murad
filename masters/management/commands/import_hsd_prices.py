from decimal import Decimal, InvalidOperation

import openpyxl
from django.core.management.base import BaseCommand, CommandError

from masters import rate_correct
from masters.models import FuelProduct, Vendor, VendorFuelPrice

HI_CETANE_NAME = "HI-CETANE DIESEL EURO5"  # PSO's own name for what this file calls "HSD"


class Command(BaseCommand):
    help = ("Import a PSO HSD price history (.xlsx with 'Fuel Effective Date' / 'Fuel Price' / 'PRODUCT' "
            "columns) into PSO Fuel Prices, under Hi-Cetane Diesel Euro5. Only ever writes VendorFuelPrice rows "
            "- Client Rates are never touched, so the Apply Fuel Price 'already applied' check is unaffected. "
            "A date already used by a Client Rate entry with a different price is skipped and listed for "
            "Correct & Recalculate on the Fuel Rates page, unless --apply-locked is passed.")

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the .xlsx file")
        parser.add_argument("--apply-locked", action="store_true",
                             help="Also overwrite dates already used in Client Rates (normally left for Correct & Recalculate)")
        parser.add_argument("--dry-run", action="store_true", help="Report what would happen, write nothing")

    def handle(self, *args, **options):
        path, dry_run, apply_locked = options["path"], options["dry_run"], options["apply_locked"]
        try:
            wb = openpyxl.load_workbook(path, data_only=True)
        except FileNotFoundError:
            raise CommandError(f"File not found: {path}")
        ws = wb.active

        header_row = next(ws.iter_rows(min_row=1, max_row=1))
        col = {}
        for cell in header_row:
            name = str(cell.value or "").strip().lower()
            if "date" in name:
                col["date"] = cell.column
            elif "price" in name:
                col["price"] = cell.column
        if "date" not in col or "price" not in col:
            raise CommandError(f"Couldn't find a date and a price column in the header row: "
                                f"{[c.value for c in header_row]}")

        pso_vendor = Vendor.objects.filter(name__iexact="PSO").first()
        if not pso_vendor:
            pso_vendor = Vendor.objects.create(name="PSO") if not dry_run else None
        hi_cetane = FuelProduct.objects.filter(name=HI_CETANE_NAME).first()
        if not hi_cetane:
            hi_cetane = FuelProduct.objects.create(name=HI_CETANE_NAME) if not dry_run else None

        added, updated, unchanged, bad_rows = 0, 0, 0, 0
        locked = []
        seen_dates = set()

        for r in range(2, ws.max_row + 1):
            eff_date_raw = ws.cell(row=r, column=col["date"]).value
            price_raw = ws.cell(row=r, column=col["price"]).value
            if eff_date_raw in (None, "") and price_raw in (None, ""):
                continue  # trailing blank row
            eff_date = eff_date_raw.date() if hasattr(eff_date_raw, "date") else eff_date_raw
            try:
                price = Decimal(str(price_raw)).quantize(Decimal("0.01"))
            except (InvalidOperation, TypeError):
                self.stdout.write(self.style.ERROR(f"  row {r}: bad price {price_raw!r} - skipped"))
                bad_rows += 1
                continue
            if eff_date in seen_dates:
                self.stdout.write(self.style.WARNING(f"  row {r}: duplicate date {eff_date} in the file - last one wins"))
            seen_dates.add(eff_date)

            existing = VendorFuelPrice.objects.filter(
                vendor=pso_vendor, product=hi_cetane, effective_date=eff_date).first() if pso_vendor and hi_cetane else None
            if existing:
                if existing.fuel_price == price:
                    unchanged += 1
                    continue
                in_use = rate_correct.rates_using(hi_cetane.id, eff_date, existing.fuel_price).exists()
                if in_use and not apply_locked:
                    locked.append((eff_date, existing.fuel_price, price))
                    continue
                self.stdout.write(f"  {eff_date}: {existing.fuel_price} -> {price}"
                                   f"{' (was used by client rates)' if in_use else ''}")
                if not dry_run:
                    existing.fuel_price = price
                    existing.save(update_fields=["fuel_price"])
                updated += 1
            else:
                self.stdout.write(f"  {eff_date}: new, {price}")
                if not dry_run:
                    VendorFuelPrice.objects.create(vendor=pso_vendor, product=hi_cetane, effective_date=eff_date, fuel_price=price)
                added += 1

        self.stdout.write(self.style.SUCCESS(
            f"{'[DRY RUN] ' if dry_run else ''}Added {added}, updated {updated}, already matching {unchanged}"
            f"{f', {bad_rows} bad row(s) skipped' if bad_rows else ''}."
        ))
        if locked:
            self.stdout.write(self.style.WARNING(
                f"{len(locked)} date(s) are already used in Client Rates with a different price and were left "
                "alone (use Correct & Recalculate on the Fuel Rates page, or re-run with --apply-locked):"
            ))
            for d, old, new in locked:
                self.stdout.write(f"  {d}: current {old}, file says {new}")
