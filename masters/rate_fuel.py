"""Client Rates > Apply Fuel Price.

Revises all of a client's rates onto a new (uploaded) fuel price in one go,
with the same formula as a hand-made entry: for every route + vehicle type +
tonnage, the latest rate becomes the base -
    Current Fuel Price = its Updated Fuel Price
    Current Rate       = its Updated Trip Cost
    Effective %        = unchanged
    Updated Fuel Price = the new fuel price, Effective Date = that price's date.
Step 1 previews every rate (old vs new trip cost); step 2 (Confirm) creates
the entries. Rates already revised on/after that date are skipped, so it can
be re-run safely.
"""
from collections import OrderedDict
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .models import Client, ClientRate, FuelProduct, FuelRateBatch, VendorFuelPrice

def _latest_rates(client, product, include_blank):
    """Latest rate per route + vehicle type + tonnage priced on `product`
    (plus, optionally, older entries saved with no fuel product)."""
    rates = ClientRate.objects.filter(client=client).select_related("route", "vehicle_type", "fuel_product", "sub_category")
    if include_blank:
        rates = rates.filter(Q(fuel_product=product) | Q(fuel_product__isnull=True))
    else:
        rates = rates.filter(fuel_product=product)
    latest = OrderedDict()
    for r in rates.order_by("-effective_date", "-id"):
        latest.setdefault((r.sub_category_id, r.route_id, r.vehicle_type_id, r.weight_tons), r)
    # Fixed rates never move with fuel - leave them out of the revision
    latest = OrderedDict((k, r) for k, r in latest.items() if r.rate_type != "FIXED")
    return sorted(latest.values(), key=lambda r: (str(r.sub_category or ""), r.route.route_code, str(r.vehicle_type or ""), r.weight_tons or 0))


def _revise(base, new_price):
    """New trip cost for `base` at `new_price` - same formula as ClientRate.save()."""
    current_fuel, current_rate, pct = base.updated_fuel_price, base.updated_trip_cost, base.effective_percent
    subject = current_rate * (pct / 100)
    change_pct = (new_price - current_fuel) / current_fuel * 100 if current_fuel else Decimal(0)
    adjustment = subject * (change_pct / 100)
    return {
        "current_fuel_price": current_fuel, "current_rate": current_rate, "effective_percent": pct,
        "rate_subject_to_revision": subject, "updated_fuel_price": new_price,
        "fuel_price_change_percent": change_pct, "rate_adjustment": adjustment,
        "updated_trip_cost": current_rate + adjustment,
    }


def _plan(client, price, include_blank):
    rows = []
    for base in _latest_rates(client, price.product, include_blank):
        row = {"base": base, "skip": ""}
        if base.effective_date >= price.effective_date:
            row["skip"] = f"Already revised on {base.effective_date:%d-%b-%y}"
        else:
            row["new"] = _revise(base, price.fuel_price)
            row["diff"] = row["new"]["updated_trip_cost"] - base.updated_trip_cost
        rows.append(row)
    return rows


def client_rate_apply_fuel(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    price = pso_fuel_prices().select_related("product").filter(pk=request.POST.get("price") or request.GET.get("price") or None).first()
    include_blank = (request.POST.get("include_blank") or request.GET.get("include_blank")) == "1"
    back = redirect("client_rates", client_id=client.id)
    if not price:
        messages.error(request, "Apply Fuel Price: choose the new fuel price first.")
        return back

    rows = _plan(client, price, include_blank)

    if request.method == "POST":
        to_create = []
        for row in rows:
            if row["skip"]:
                continue
            base = row["base"]
            to_create.append(ClientRate(
                client=client, sub_category_id=base.sub_category_id, route_id=base.route_id,
                vehicle_type_id=base.vehicle_type_id,
                weight_tons=base.weight_tons, fuel_product=price.product,
                effective_date=price.effective_date, **row["new"],
            ))
        with transaction.atomic():
            if to_create:
                batch = FuelRateBatch.objects.create(
                    client=client, product=price.product, fuel_price=price.fuel_price,
                    effective_date=price.effective_date, rate_count=len(to_create),
                    created_by=request.user if request.user.is_authenticated else None)
                for rate in to_create:
                    rate.fuel_batch = batch
            # Values are worked out above from each rate's own latest entry;
            # bulk_create keeps ClientRate.save() from re-picking the base.
            ClientRate.objects.bulk_create(to_create)
        from operations.models import refresh_trip_freight
        for c in to_create:
            refresh_trip_freight(c.client_id, c.route_id, c.vehicle_type_id, c.weight_tons, c.sub_category_id)
        skipped = len(rows) - len(to_create)
        if to_create:
            messages.success(request, f"Updated {len(to_create)} rate(s) to {price.product.name} "
                             f"{price.fuel_price} effective {price.effective_date:%d-%b-%y}."
                             + (f" {skipped} already up to date, left as is." if skipped else ""))
        else:
            messages.info(request, "Nothing to update - all rates are already on this or a newer fuel price.")
        return back

    # Which fuel prices the rates are on today (usually one group)
    basis = OrderedDict()
    for row in rows:
        b = row["base"]
        key = (b.updated_fuel_price, b.effective_date)
        basis[key] = basis.get(key, 0) + 1
    return render(request, "clients/client_rates_apply_fuel.html", {
        "client": client, "price": price, "rows": rows, "include_blank": include_blank,
        "basis": [(p, d, n) for (p, d), n in sorted(basis.items(), key=lambda kv: kv[0][1], reverse=True)],
        "to_update": sum(1 for r in rows if not r["skip"]),
        "back_url": reverse("client_rates", args=[client.id]),
    })


def _blocking(rate):
    """True if a newer entry has been made on top of this one (same route /
    type / tonnage) - undoing it would pull the ground out from under that."""
    return ClientRate.objects.filter(
        client_id=rate.client_id, route_id=rate.route_id, vehicle_type_id=rate.vehicle_type_id,
        weight_tons=rate.weight_tons, sub_category_id=rate.sub_category_id,
    ).filter(Q(effective_date__gt=rate.effective_date) | Q(effective_date=rate.effective_date, id__gt=rate.id)).exists()


def client_rate_fuel_undo(request, client_id, batch_id):
    """Undo one Apply Fuel Price run: delete the entries it created, which
    puts every rate (and the trips priced off them) back where it was."""
    client = get_object_or_404(Client, id=client_id)
    batch = get_object_or_404(FuelRateBatch, id=batch_id, client=client)
    back = redirect("client_rates", client_id=client.id)
    if request.method != "POST":
        return back
    rates = list(batch.rates.all())
    blocked = [r for r in rates if _blocking(r)]
    if blocked:
        messages.error(request, f"Can't undo the {batch.fuel_price} ({batch.effective_date:%d-%b-%y}) update: "
                       f"{len(blocked)} of its rate(s) already have newer entries on top. Undo the newer update first.")
        return back
    with transaction.atomic():
        # Deleting each rate re-prices its trips (ClientRate post_delete signal)
        for rate in rates:
            rate.delete()
        batch.delete()
    messages.success(request, f"Undone: fuel price {batch.fuel_price} effective {batch.effective_date:%d-%b-%y} - "
                     f"{len(rates)} rate entr{'y' if len(rates) == 1 else 'ies'} removed, rates and trip charges are back to before.")
    return back


def pso_fuel_prices():
    """The official PSO prices entered on Suppliers > Fuel Rates - the index
    client rates are revised on. Prices a supplier/pump has on its own vendor
    form are purchase prices, not the index, and are left out."""
    return VendorFuelPrice.objects.filter(vendor__name__iexact="PSO")


def fuel_price_choices(client):
    """For the Apply Fuel Price window: every PSO fuel price (newest first) by
    product, plus how many of the client's rates have no fuel product set."""
    prices = pso_fuel_prices().select_related("product").order_by("-effective_date", "-id")
    products = FuelProduct.objects.filter(pk__in=prices.values("product_id")).order_by("name")
    return {
        "fuel_products": products,
        "fuel_prices": prices,
        "fuel_batches": FuelRateBatch.objects.filter(client=client).select_related("product", "created_by")[:5],
        "blank_product_rates": ClientRate.objects.filter(client=client, fuel_product__isnull=True).count(),
    }
