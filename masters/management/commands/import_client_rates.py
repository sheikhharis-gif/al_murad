from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from masters.models import Client, ClientRate, Route, VehicleType


DEFAULT_EFFECTIVE_DATE = date(2026, 10, 1)
CENT = Decimal("0.01")


def _header(value):
    return " ".join(str(value or "").strip().lower().replace("_", " ").split())


def _decimal(value, row_number, label):
    try:
        result = Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        raise CommandError(f"Row {row_number}: {label} is not a valid number: {value!r}")
    if not result.is_finite():
        raise CommandError(f"Row {row_number}: {label} must be a finite number.")
    return result


class Command(BaseCommand):
    help = "Import a client's fixed route rates from an Excel workbook."

    def add_arguments(self, parser):
        parser.add_argument("client_name", help="Client name as registered in the app.")
        parser.add_argument("file", help="Workbook path, absolute or relative to the project folder.")
        parser.add_argument(
            "--effective-date", default=DEFAULT_EFFECTIVE_DATE.isoformat(),
            help="Rate effective date in YYYY-MM-DD format (default: 2026-10-01).",
        )
        parser.add_argument(
            "--apply", action="store_true",
            help="Save valid rows. Without this flag, only show the import preview.",
        )

    def handle(self, *args, **options):
        file_path = Path(options["file"])
        if not file_path.is_absolute():
            file_path = Path(settings.BASE_DIR) / file_path
        if not file_path.is_file():
            raise CommandError(f"Workbook not found: {file_path}")
        try:
            effective_date = date.fromisoformat(options["effective_date"])
        except ValueError:
            raise CommandError("Effective date must use YYYY-MM-DD format.")

        client = Client.objects.filter(name__iexact=options["client_name"]).first()
        if not client:
            raise CommandError(f"Client '{options['client_name']}' was not found. Create the client first.")

        try:
            workbook = load_workbook(file_path, read_only=True, data_only=True)
        except Exception as exc:
            raise CommandError(f"Could not read workbook: {exc}") from exc
        sheet = workbook.active
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows, None)
        if not headers:
            raise CommandError("The workbook's first sheet is empty.")
        columns = {_header(value): index for index, value in enumerate(headers)}
        required = {"route", "veh type", "tonnage", "rates"}
        missing_columns = required - columns.keys()
        if missing_columns:
            raise CommandError("Missing workbook columns: " + ", ".join(sorted(missing_columns)))

        prepared, seen = [], set()
        for row_number, values in enumerate(rows, start=2):
            if not values or not any(value is not None for value in values):
                continue
            route_code = str(values[columns["route"]] or "").strip().upper()
            vehicle_name = str(values[columns["veh type"]] or "").strip().upper()
            if not route_code or not vehicle_name:
                self.stderr.write(self.style.WARNING(f"Row {row_number}: missing route or vehicle type; skipped."))
                continue
            weight = _decimal(values[columns["tonnage"]], row_number, "tonnage")
            amount = _decimal(values[columns["rates"]], row_number, "rate")
            key = (route_code, vehicle_name, weight)
            if key in seen:
                self.stderr.write(self.style.WARNING(
                    f"DUPLICATE IN WORKBOOK: {route_code} / {vehicle_name} / {weight} tons; skipped row {row_number}."
                ))
                continue
            seen.add(key)

            route = Route.objects.filter(route_code__iexact=route_code).select_related("origin", "destination").first()
            if not route:
                self.stderr.write(self.style.WARNING(f"MISSING ROUTE: {route_code} (row {row_number})."))
                continue
            vehicle_type = VehicleType.objects.filter(name__iexact=vehicle_name).first()
            if not vehicle_type:
                self.stderr.write(self.style.WARNING(f"MISSING VEHICLE TYPE: {vehicle_name} (row {row_number})."))
                continue

            duplicate = ClientRate.objects.filter(
                client=client, route=route, vehicle_type=vehicle_type, weight_tons=weight,
                effective_date=effective_date, sub_category__isnull=True,
            ).exists()
            if duplicate:
                self.stderr.write(self.style.WARNING(
                    f"ALREADY EXISTS: {route_code} / {vehicle_name} / {weight} tons on {effective_date}; skipped."
                ))
                continue
            prepared.append({
                "route": route, "vehicle_type": vehicle_type, "weight": weight,
                "amount": amount, "route_code": route_code,
            })

        self.stdout.write(
            f"Client: {client.name} | Effective: {effective_date} | Valid rows: {len(prepared)}"
        )
        self.stdout.write(
            "Importing the workbook's 'rates' values as fixed fares; fuel revision columns are not applied."
        )
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Preview only. Add --apply to save these rates."))
            return

        with transaction.atomic():
            for row in prepared:
                ClientRate.objects.create(
                    client=client,
                    rate_type="FIXED",
                    route=row["route"],
                    current_rate=row["amount"],
                    effective_percent=Decimal("0"),
                    current_fuel_price=Decimal("0"),
                    updated_fuel_price=Decimal("0"),
                    weight_tons=row["weight"],
                    vehicle_type=row["vehicle_type"],
                    effective_date=effective_date,
                )

        self.stdout.write(self.style.SUCCESS(f"Imported {len(prepared)} fixed rate(s) for {client.name}."))
