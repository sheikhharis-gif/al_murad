"""Load the client's "Asset Data" sheet into Vehicles.

    python manage.py import_asset_data "Asset Data.xlsx" --dry-run   # show what would change
    python manage.py import_asset_data "Asset Data.xlsx"             # save it

One row per vehicle, matched on Vehicle Number: a new number creates the
vehicle, an existing one is updated from the sheet's filled-in cells only (a
blank cell never wipes what's already saved). Current KMs never goes down -
trips may already have moved a vehicle's odometer past the sheet's figure.
Safe to re-run.
"""
import datetime as dt
from decimal import Decimal, InvalidOperation

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from openpyxl import load_workbook

from masters.models import Client, Staff, Vehicle, VehicleType, Wheeler

# Sheet header -> how to read it
HEADERS = {
    "mode": "Mode", "number": "Vehicle Number", "owner": "Owner", "make": "Make", "model": "Model",
    "type": "Type", "wheeler": "Wheeler", "color": "Vehicle Color", "chassis": "Chassis No",
    "engine": "Engine No", "weight": "Weight Capacity", "purchase": "Purchase Date", "value": "Value",
    "mtag": "M-Tag #", "start_km": "Starting KMs", "current_km": "Current KMs",
    "client": "Dedicated to Client", "leased": "Leased", "container": "Container No",
    "reg_name": "Registration Name", "driver1": "Driver 1", "driver2": "Driver 2",
}


def _text(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    s = str(v).strip()
    return "" if s.upper() in ("", "-", "NOT DEFINE", "N/A", "NONE") else s


def _int(v):
    try:
        return int(float(str(v).replace(",", ""))) if _text(v) else None
    except ValueError:
        return None


def _decimal(v):
    try:
        return Decimal(str(v).replace(",", "")) if _text(v) else None
    except InvalidOperation:
        return None


def _date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = _text(v)
    for fmt in ("%d-%b-%y", "%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    return None


class Command(BaseCommand):
    help = "Import / update Vehicles from the Asset Data Excel sheet (matched on Vehicle Number)."

    def add_arguments(self, parser):
        parser.add_argument("path", help="Path to the .xlsx file")
        parser.add_argument("--dry-run", action="store_true", help="Show what would change without saving")

    def handle(self, path, dry_run=False, **options):
        try:
            ws = load_workbook(path, data_only=True).worksheets[0]
        except Exception as exc:
            raise CommandError(f"Can't open {path}: {exc}")
        rows = list(ws.iter_rows(values_only=True))
        header = [str(h).strip() if h is not None else "" for h in rows[0]]
        col = {}
        for key, name in HEADERS.items():
            if name in header:
                col[key] = header.index(name)
        if "number" not in col:
            raise CommandError("The sheet has no 'Vehicle Number' column.")

        created = updated = unchanged = 0
        notes = []
        with transaction.atomic():
            for line, row in enumerate(rows[1:], start=2):
                get = lambda k: row[col[k]] if k in col and col[k] < len(row) else None
                number = _text(get("number")).upper()
                if not number:
                    continue
                vehicle = Vehicle.objects.filter(vehicle_number__iexact=number).first()
                is_new = vehicle is None
                if is_new:
                    vehicle = Vehicle(vehicle_number=number)
                before = {f.attname: getattr(vehicle, f.attname) for f in Vehicle._meta.concrete_fields}

                def put(field, value):
                    if value not in (None, ""):
                        setattr(vehicle, field, value)

                mode = _text(get("mode")).upper()
                put("vehicle_mode", "RENTAL" if mode.startswith("RENT") else ("OWN" if mode else None))
                put("owner", _text(get("owner")))
                put("make", _text(get("make")))
                put("model_year", _int(get("model")))
                put("color", _text(get("color")))
                put("chassis_no", _text(get("chassis")))
                put("engine_no", _text(get("engine")))
                weight = _decimal(get("weight"))
                if weight:  # 0 in the sheet = not known
                    put("weight_capacity", format(weight.normalize(), "f"))
                put("purchase_date", _date(get("purchase")))
                value = _decimal(get("value"))
                if value:
                    put("value", value)
                put("m_tag", _text(get("mtag")))
                put("container_no", _text(get("container")))
                put("registration_name", _text(get("reg_name")))
                if _text(get("leased")):
                    vehicle.leased = _text(get("leased")).upper() in ("YES", "Y", "TRUE", "1")

                vtype = _text(get("type")).upper()
                if vtype:
                    vehicle.vehicle_type, _ = VehicleType.objects.get_or_create(name=vtype)
                wheels = _text(get("wheeler")).upper()
                if wheels:
                    label = f"{wheels} WHEELER" if wheels.isdigit() else wheels
                    vehicle.wheeler, _ = Wheeler.objects.get_or_create(name=label)

                start_km, current_km = _int(get("start_km")), _int(get("current_km"))
                if start_km is not None and (is_new or not vehicle.starting_km):
                    vehicle.starting_km = start_km
                if current_km is not None and current_km > (vehicle.current_km or 0):
                    vehicle.current_km = current_km  # never lower an odometer trips have moved on

                client_name = _text(get("client"))
                if client_name:
                    client = Client.objects.filter(name__iexact=client_name).first()
                    if client:
                        vehicle.dedicated_client = client
                    else:
                        notes.append(f"row {line} {number}: client '{client_name}' not found - left blank")
                for key, field in (("driver1", "driver"), ("driver2", "driver2")):
                    name = _text(get(key))
                    if name:
                        staff = Staff.objects.filter(name__iexact=name).first()
                        if staff:
                            setattr(vehicle, field, staff)
                        else:
                            notes.append(f"row {line} {number}: driver '{name}' not found in Staff - left blank")

                vehicle.save()
                after = {f.attname: getattr(vehicle, f.attname) for f in Vehicle._meta.concrete_fields}
                if is_new:
                    created += 1
                    self.stdout.write(f"  + {number}  {vtype}  {_text(get('owner'))}")
                elif before != after:
                    updated += 1
                    changed = [k for k in after if before[k] != after[k]]
                    self.stdout.write(f"  ~ {number}  updated: {', '.join(changed)}")
                else:
                    unchanged += 1

            for n in notes:
                self.stdout.write(self.style.WARNING("  ! " + n))
            summary = f"{created} vehicle(s) added, {updated} updated, {unchanged} already up to date."
            if dry_run:
                transaction.set_rollback(True)
                self.stdout.write(self.style.WARNING("DRY RUN - nothing saved. " + summary))
            else:
                self.stdout.write(self.style.SUCCESS(summary))
