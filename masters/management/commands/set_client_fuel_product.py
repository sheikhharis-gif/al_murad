"""Set the Fuel Product (e.g. DIESEL) on a client's rates that have none.

    python manage.py set_client_fuel_product "RED BULL" DIESEL                 # preview
    python manage.py set_client_fuel_product "RED BULL" DIESEL --apply         # do it
    python manage.py set_client_fuel_product "RED BULL" DIESEL --all --apply   # also overwrite other products

Only rates with no Fuel Product are changed unless --all is given. Prices are not touched.
"""
from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from masters.management.commands.move_client_rates import _client
from masters.models import ClientRate, FuelProduct


class Command(BaseCommand):
    help = "Set a Fuel Product on a client's rates (preview unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("client")
        parser.add_argument("product")
        parser.add_argument("--all", action="store_true", help="Also change rates that already have a product.")
        parser.add_argument("--apply", action="store_true", help="Save. Without it, preview only.")

    def handle(self, *args, **options):
        client = _client(options["client"])
        product = FuelProduct.objects.filter(name__iexact=options["product"].strip()).first()
        if not product:
            names = ", ".join(FuelProduct.objects.values_list("name", flat=True)) or "none"
            raise CommandError(f"Fuel product '{options['product']}' not found. Available: {names}")
        rates = ClientRate.objects.filter(client=client)
        counts = Counter(str(p) for p in rates.values_list("fuel_product__name", flat=True))
        self.stdout.write(f"{client.name}: {rates.count()} rate(s); fuel product now: {dict(counts)}")
        target = rates if options["all"] else rates.filter(fuel_product__isnull=True)
        target = target.exclude(fuel_product=product)
        n = target.count()
        self.stdout.write(f"{n} rate(s) to set to {product.name}.")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("Preview only. Add --apply to save."))
            return
        target.update(fuel_product=product)
        self.stdout.write(self.style.SUCCESS(f"Set {product.name} on {n} rate(s) of {client.name}."))
