from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.core.management.base import BaseCommand
from django.db import connection, transaction


class Command(BaseCommand):
    help = "Repair malformed ClientRate numeric values and recalculate derived totals."

    numeric_limits = {
        "current_fuel_price": 20,
        "current_rate": 20,
        "effective_percent": 10,
        "updated_fuel_price": 20,
        "weight_tons": 12,
    }

    def clean_decimal(self, value, max_digits, nullable=False):
        if value in (None, ""):
            return None if nullable else Decimal("0.00")
        try:
            number = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            if not number.is_finite():
                raise InvalidOperation
        except (InvalidOperation, ValueError, TypeError):
            return None if nullable else Decimal("0.00")

        integer_digits = max_digits - 2
        maximum = (Decimal(10) ** integer_digits) - Decimal("0.01")
        if abs(number) > maximum:
            return Decimal("0.00")
        return number

    def handle(self, *args, **options):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id, current_fuel_price, current_rate, effective_percent, "
                    "updated_fuel_price, weight_tons FROM masters_clientrate"
                )
                rows = cursor.fetchall()
                repaired = 0
                for row in rows:
                    row_id, current_fuel, current_rate, effective_percent, updated_fuel, weight = row
                    current_fuel = self.clean_decimal(current_fuel, 20)
                    current_rate = self.clean_decimal(current_rate, 20)
                    effective_percent = self.clean_decimal(effective_percent, 10)
                    updated_fuel = self.clean_decimal(updated_fuel, 20)
                    weight = self.clean_decimal(weight, 12, nullable=True)

                    revision = current_rate * (effective_percent / Decimal("100"))
                    fuel_change = (
                        (updated_fuel - current_fuel) / current_fuel * Decimal("100")
                        if current_fuel else Decimal("0")
                    )
                    adjustment = revision * (fuel_change / Decimal("100"))
                    updated_trip_cost = current_rate + adjustment

                    values = [
                        current_fuel, current_rate, effective_percent, revision,
                        updated_fuel, fuel_change, adjustment, updated_trip_cost, weight, row_id,
                    ]
                    cursor.execute(
                        "UPDATE masters_clientrate SET "
                        "current_fuel_price=?, current_rate=?, effective_percent=?, "
                        "rate_subject_to_revision=?, updated_fuel_price=?, "
                        "fuel_price_change_percent=?, rate_adjustment=?, updated_trip_cost=?, "
                        "weight_tons=? WHERE id=?",
                        values,
                    )
                    repaired += 1

        self.stdout.write(self.style.SUCCESS(f"Repaired {repaired} ClientRate row(s)."))
