from datetime import date
from decimal import Decimal, InvalidOperation

import openpyxl
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from masters import rate_correct
from masters.models import FuelProduct, Vendor, VendorFuelPrice

# file column -> PSO product it is saved under
PRODUCTS = {"petrol": "PREMIER EURO5", "diesel": "HI-CETANE DIESEL EURO5"}


def _price(value):
    try:
        p = Decimal(str(value)).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError):
        return None
    return p if p > 0 else None


class Command(BaseCommand):
    help = ("Fuel Rate list (.xlsx with 'Date', 'Petrol', 'Diesel' columns) -> PSO Fuel Prices: Petrol under "
            "Premier Euro5, Diesel under Hi-Cetane Diesel Euro5, each saved separately. Blank / 0 / error cells "
            "are skipped. A date already used by Client Rates with a different price is left alone and listed "
            "(fix it with Correct & Recalculate). Client Rates are never touched. Preview by default; --apply saves.")

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--apply", action="store_true")

    def read(self, path):
        try:
            ws = openpyxl.load_workbook(path, data_only=True).active
        except FileNotFoundError:
            raise CommandError(f"File not found: {path}")
        rows, cols = [], None
        for r in ws.iter_rows(values_only=True):
            labels = [str(c).strip().lower() if c is not None else "" for c in r]
            if cols is None:
                if "date" in labels and ("petrol" in labels or "diesel" in labels):
                    cols = {k: labels.index(k) for k in ("date", "petrol", "diesel") if k in labels}
                continue
            d = r[cols["date"]]
            if not hasattr(d, "year"):
                continue
            d = d.date() if hasattr(d, "date") else d
            rows.append([d, {k: _price(r[cols[k]]) for k in PRODUCTS if k in cols}])
        if cols is None:
            raise CommandError("No header row with 'Date' and 'Petrol' / 'Diesel' found.")
        # a typo'd year between two rows of the same year (e.g. 2022-10-23 among 2026 dates) takes their year
        for i in range(1, len(rows) - 1):
            prev, cur, nxt = rows[i - 1][0], rows[i][0], rows[i + 1][0]
            if prev.year == nxt.year != cur.year:
                fixed = date(prev.year, cur.month, cur.day)
                if prev <= fixed <= nxt:
                    self.stdout.write(self.style.WARNING(f"  {cur} looks like a typo - read as {fixed}"))
                    rows[i][0] = fixed
        return rows

    def handle(self, *args, **opts):
        rows = self.read(opts["path"])
        vendor = Vendor.objects.filter(name__iexact="PSO").first()
        if not vendor:
            raise CommandError("No supplier named PSO.")
        products = {}
        for key, name in PRODUCTS.items():
            products[key] = FuelProduct.objects.filter(name=name).first()
            if not products[key]:
                raise CommandError(f"Fuel product {name} not found.")

        add, upd, same, locked = [], [], 0, []
        for d, prices in rows:
            for key, price in prices.items():
                if price is None:
                    continue
                product = products[key]
                existing = VendorFuelPrice.objects.filter(vendor=vendor, product=product, effective_date=d).first()
                if not existing:
                    add.append((product, d, price))
                elif existing.fuel_price == price:
                    same += 1
                elif rate_correct.rates_using(product.id, d, existing.fuel_price).exists():
                    locked.append((product.name, d, existing.fuel_price, price))
                else:
                    upd.append((existing, price))

        for name in PRODUCTS.values():
            n_add = sum(1 for p, _, _ in add if p.name == name)
            n_upd = sum(1 for e, _ in upd if e.product.name == name)
            self.stdout.write(f"{name}: {n_add} new, {n_upd} changed")
        for p, d, price in add:
            self.stdout.write(f"   new      {d}  {p.name:<24} {price}")
        for e, price in upd:
            self.stdout.write(f"   change   {e.effective_date}  {e.product.name:<24} {e.fuel_price} -> {price}")
        self.stdout.write(f"Already the same: {same}")
        if locked:
            self.stdout.write(self.style.WARNING(
                f"{len(locked)} price(s) are used by Client Rates and differ from the file - left alone "
                "(use Correct & Recalculate on the Fuel Rates page):"))
            for name, d, old, new in locked:
                self.stdout.write(f"   {d}  {name}: system {old}, file {new}")
        if not opts["apply"]:
            self.stdout.write("Preview only - add --apply to save.")
            return
        with transaction.atomic():
            for p, d, price in add:
                VendorFuelPrice.objects.create(vendor=vendor, product=p, effective_date=d, fuel_price=price)
            for e, price in upd:
                e.fuel_price = price
                e.save(update_fields=["fuel_price"])
        self.stdout.write(self.style.SUCCESS(f"Saved: {len(add)} new, {len(upd)} changed."))
