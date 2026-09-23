"""Suppliers > Fuel Rates: correcting a PSO fuel price that client rates already use.

Every client rate entry is chained to the one before it (Current Fuel Price /
Current Rate = the previous entry's Updated Fuel Price / Updated Trip Cost), so
a wrong fuel price on, say, 12-Aug also makes every later entry wrong. Such a
price is locked on the Fuel Rates page; changing it goes through here instead:

1. Preview - for every client / route / vehicle type / tonnage using that price,
   the entries from that date onwards, date by date, old vs corrected trip cost.
2. Confirm - the price is corrected and each chain is recalculated in date
   order: the entries on that date get the correct fuel price, every later
   entry keeps its own fuel price and Effective % but is rebuilt from the
   corrected entry before it. Entries before that date are not touched. Trips
   on/after that date are re-priced (each trip uses the rate in force on its date).
"""
from collections import OrderedDict
from datetime import date as date_cls
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.urls import reverse

from .models import ClientRate, FuelProduct, FuelRateBatch, VendorFuelPrice

CENT = Decimal("0.01")


def rates_using(product_id, eff_date, price):
    """Client rate entries built on this PSO price: that date, that fuel price,
    on that product (or saved with no fuel product)."""
    return ClientRate.objects.filter(effective_date=eff_date, updated_fuel_price=price).filter(
        Q(fuel_product_id=product_id) | Q(fuel_product__isnull=True))


def usage_counts():
    """{(effective_date, product_id or None, price): number of rate entries} for the Fuel Rates table."""
    counts = {}
    for row in ClientRate.objects.values("effective_date", "fuel_product_id", "updated_fuel_price").annotate(n=Count("id")):
        key = (row["effective_date"], row["fuel_product_id"], row["updated_fuel_price"])
        counts[key] = counts.get(key, 0) + row["n"]
    return counts


def used_count(counts, eff_date, product_id, price):
    if price is None:
        return 0
    price = Decimal(price)
    return counts.get((eff_date, product_id, price), 0) + counts.get((eff_date, None, price), 0)


def _calc(current_fuel, current_rate, pct, updated_fuel):
    """Same formula as ClientRate.save()."""
    subject = current_rate * (pct / 100)
    change = (updated_fuel - current_fuel) / current_fuel * 100 if current_fuel else Decimal(0)
    adjustment = subject * (change / 100)
    return {
        "current_fuel_price": current_fuel.quantize(CENT), "current_rate": current_rate.quantize(CENT),
        "rate_subject_to_revision": subject.quantize(CENT), "updated_fuel_price": updated_fuel,
        "fuel_price_change_percent": change.quantize(CENT), "rate_adjustment": adjustment.quantize(CENT),
        "updated_trip_cost": (current_rate + adjustment).quantize(CENT),
    }


def plan_correction(product_id, eff_date, old_price, new_price):
    """Chains affected by correcting (product, date) from old_price to new_price,
    each with its entries from that date on and their corrected values."""
    from operations.models import Trip
    affected = list(rates_using(product_id, eff_date, old_price))
    affected_ids = {r.id for r in affected}
    keys = OrderedDict()
    for r in affected:
        keys.setdefault((r.client_id, r.route_id, r.vehicle_type_id, r.weight_tons), r)

    chains = []
    for (client_id, route_id, vt_id, weight), sample in keys.items():
        entries = ClientRate.objects.filter(
            client_id=client_id, route_id=route_id, vehicle_type_id=vt_id, weight_tons=weight,
            effective_date__gte=eff_date,
        ).filter(Q(fuel_product_id=product_id) | Q(fuel_product__isnull=True)).select_related(
            "client", "route", "vehicle_type").order_by("effective_date", "id")
        rows, prev = [], None
        for e in entries:
            updated_fuel = new_price if e.id in affected_ids else e.updated_fuel_price
            current_fuel = prev["updated_fuel_price"] if prev else e.current_fuel_price
            current_rate = prev["updated_trip_cost"] if prev else e.current_rate
            new = _calc(current_fuel, current_rate, e.effective_percent, updated_fuel)
            rows.append({"rate": e, "new": new, "diff": new["updated_trip_cost"] - e.updated_trip_cost,
                         "is_corrected_date": e.id in affected_ids})
            prev = new
        trips = Trip.objects.filter(client_id=client_id, route_id=route_id, vehicle_type_id=vt_id,
                                    weight=weight, trip_date__gte=eff_date).count()
        chains.append({"sample": sample, "rows": rows, "trips": trips})
    chains.sort(key=lambda c: (c["sample"].client.name, c["sample"].route.route_code,
                               str(c["sample"].vehicle_type or ""), c["sample"].weight_tons or 0))
    return chains


def _pso_price(product_id, eff_date):
    return VendorFuelPrice.objects.filter(vendor__name__iexact="PSO", product_id=product_id,
                                          effective_date=eff_date).select_related("product").first()


def fuel_price_correct(request):
    back = redirect("fuel_rates")
    try:
        product = FuelProduct.objects.get(pk=request.POST.get("product") or request.GET.get("product"))
        eff_date = date_cls.fromisoformat(request.POST.get("date") or request.GET.get("date") or "")
        new_price = Decimal(request.POST.get("price") or request.GET.get("price") or "").quantize(CENT)
    except Exception:
        messages.error(request, "Correct fuel price: missing or invalid product / date / price.")
        return back
    pso = _pso_price(product.id, eff_date)
    if not pso:
        messages.error(request, f"No PSO {product.name} price on {eff_date:%d-%b-%y} to correct.")
        return back
    old_price = pso.fuel_price
    if new_price == old_price:
        messages.info(request, f"{product.name} on {eff_date:%d-%b-%y} is already {old_price} - nothing to correct.")
        return back

    chains = plan_correction(product.id, eff_date, old_price, new_price)

    if request.method == "POST":
        from operations.models import refresh_trip_freight
        with transaction.atomic():
            for chain in chains:
                for row in chain["rows"]:
                    fields = dict(row["new"])
                    if row["is_corrected_date"]:
                        fields["fuel_product"] = product  # older entries had none
                    ClientRate.objects.filter(pk=row["rate"].pk).update(**fields)
            pso.fuel_price = new_price
            pso.save(update_fields=["fuel_price"])
            FuelRateBatch.objects.filter(product=product, effective_date=eff_date, fuel_price=old_price).update(
                fuel_price=new_price)
        repriced = 0
        for chain in chains:
            s = chain["sample"]
            repriced += refresh_trip_freight(s.client_id, s.route_id, s.vehicle_type_id, s.weight_tons)
        entries = sum(len(c["rows"]) for c in chains)
        messages.success(request, f"Corrected {product.name} on {eff_date:%d-%b-%y}: {old_price} -> {new_price}. "
                         f"{entries} rate entr{'y' if entries == 1 else 'ies'} recalculated date by date, "
                         f"{repriced} trip(s) re-priced.")
        return back

    return render(request, "vendors/fuel_price_correct.html", {
        "product": product, "eff_date": eff_date, "old_price": old_price, "new_price": new_price,
        "chains": chains,
        "entry_count": sum(len(c["rows"]) for c in chains),
        "client_count": len({c["sample"].client_id for c in chains}),
        "trip_count": sum(c["trips"] for c in chains),
        "back_url": reverse("fuel_rates"),
    })
