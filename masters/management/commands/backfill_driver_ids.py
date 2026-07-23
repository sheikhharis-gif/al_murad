from django.core.management.base import BaseCommand

from masters.models import Driver


class Command(BaseCommand):
    help = (
        "Assigns an Employee ID to any Driver row that's missing one "
        "(blank employee_id). Safe to re-run - does nothing once every "
        "driver already has an ID."
    )

    def handle(self, *args, **options):
        missing = Driver.objects.filter(employee_id="").order_by("id")
        count = missing.count()
        for driver in missing:
            driver.save()  # Driver.save() assigns the next ALMRD-#### automatically.

        self.stdout.write(self.style.SUCCESS(
            f"Assigned Employee ID to {count} driver(s) that were missing one."
        ))
