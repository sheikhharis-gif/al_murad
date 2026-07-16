import csv
from django.core.management.base import BaseCommand
from masters.models import City   # ✅ masters app

class Command(BaseCommand):
    help = "Import cities from CSV"

    def handle(self, *args, **kwargs):
        with open("cities.csv", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            for row in reader:
                city, created = City.objects.get_or_create(
                    code=row["code"],
                    defaults={
                        "name": row["name"],
                        "latitude": row["latitude"],
                        "longitude": row["longitude"],
                    }
                )

                if created:
                    self.stdout.write(self.style.SUCCESS(f"Added {city.name}"))
                else:
                    self.stdout.write(f"Skipped {city.name}")

        self.stdout.write(self.style.SUCCESS("✅ Cities import completed"))
