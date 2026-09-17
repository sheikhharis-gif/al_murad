from django.core.management.base import BaseCommand

from masters.models import FuelProduct, ClientRate, VendorFuelPrice

PREMIER_NAME = "PREMIER EURO5"
HI_CETANE_NAME = "HI-CETANE DIESEL EURO5"

# Old generic products merged into the two the client actually uses.
# DIESEL/HSD -> HI-CETANE DIESEL EURO5 (their real Client Rate entries move
# with it); PETROL -> PREMIER EURO5. Old VendorFuelPrice history under these
# names is dropped rather than relabeled - those numbers don't map cleanly
# onto the new products, fresh prices get entered going forward.
DIESEL_LIKE = ["DIESEL", "HSD"]
PETROL_LIKE = ["PETROL"]


class Command(BaseCommand):
    help = f"Restrict the FuelProduct catalog to exactly '{PREMIER_NAME}' and '{HI_CETANE_NAME}'."

    def handle(self, *args, **options):
        premier, _ = FuelProduct.objects.get_or_create(name=PREMIER_NAME)

        hi_cetane = FuelProduct.objects.filter(name="HI CETANE DIESEL").first()
        if hi_cetane:
            hi_cetane.name = HI_CETANE_NAME
            hi_cetane.save()
            self.stdout.write(f"Renamed 'HI CETANE DIESEL' -> '{HI_CETANE_NAME}'.")
        else:
            hi_cetane, _ = FuelProduct.objects.get_or_create(name=HI_CETANE_NAME)

        moved_rates = 0
        removed_products = []

        for name in DIESEL_LIKE:
            product = FuelProduct.objects.filter(name=name).first()
            if not product or product.pk == hi_cetane.pk:
                continue
            moved_rates += ClientRate.objects.filter(fuel_product=product).update(fuel_product=hi_cetane)
            VendorFuelPrice.objects.filter(product=product).delete()
            product.delete()
            removed_products.append(name)

        for name in PETROL_LIKE:
            product = FuelProduct.objects.filter(name=name).first()
            if not product or product.pk == premier.pk:
                continue
            moved_rates += ClientRate.objects.filter(fuel_product=product).update(fuel_product=premier)
            VendorFuelPrice.objects.filter(product=product).delete()
            product.delete()
            removed_products.append(name)

        remaining = list(FuelProduct.objects.order_by("name").values_list("name", flat=True))
        self.stdout.write(self.style.SUCCESS(
            f"Done. Moved {moved_rates} Client Rate row(s), removed products: {removed_products or 'none'}. "
            f"Remaining catalog: {remaining}."
        ))
