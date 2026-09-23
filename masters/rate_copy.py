"""Client Rates > Copy Rates.

Rates are defined on the market-standard sizes (16FT, 20FT...) and copied
onto the modified sizes (17FT, 22FT, 24FT...) of the same kind (DRY -> DRY,
REEFER -> REEFER). For every route + fuel product + tonnage, the source type's
latest rate is copied as-is (same fuel prices, trip cost and effective date).
A target that already has a rate for that key dated on/after the source's is
left alone, so copying twice never duplicates, and copying again after the
source is revised brings the new rate across.
"""
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect

from .models import Client, ClientRate, VehicleType

# Stored columns copied verbatim (including the computed ones - the copy must
# carry the source's exact trip cost, not be re-chained off the target's history)
COPY_FIELDS = [
    "route_id", "fuel_product_id", "current_fuel_price", "current_rate", "effective_percent",
    "rate_subject_to_revision", "updated_fuel_price", "fuel_price_change_percent",
    "rate_adjustment", "updated_trip_cost", "weight_tons", "effective_date",
]


def _latest_by_key(rates):
    """Latest entry per (route, fuel product, weight) - rates must be ordered newest first."""
    latest = {}
    for r in rates:
        latest.setdefault((r.route_id, r.fuel_product_id, r.weight_tons), r)
    return latest


def copy_rates(client, source_type, target_types):
    """Returns (copied, skipped) counts."""
    source = _latest_by_key(
        ClientRate.objects.filter(client=client, vehicle_type=source_type).order_by("-effective_date", "-id"))
    to_create, skipped = [], 0
    for target in target_types:
        existing = _latest_by_key(
            ClientRate.objects.filter(client=client, vehicle_type=target).order_by("-effective_date", "-id"))
        for key, rate in source.items():
            current = existing.get(key)
            if current and current.effective_date >= rate.effective_date:
                skipped += 1
                continue
            copy = ClientRate(client=client, vehicle_type=target)
            for field in COPY_FIELDS:
                setattr(copy, field, getattr(rate, field))
            to_create.append(copy)
    # bulk_create skips ClientRate.save(), which would otherwise re-base the
    # copy on the target type's previous revision instead of the source's rate.
    ClientRate.objects.bulk_create(to_create)
    # bulk_create sends no signals - re-price the trips these copies apply to
    from operations.models import refresh_trip_freight
    for key in {(c.client_id, c.route_id, c.vehicle_type_id, c.weight_tons) for c in to_create}:
        refresh_trip_freight(*key)
    return len(to_create), skipped


def client_rate_copy(request, client_id):
    client = get_object_or_404(Client, id=client_id)
    if request.method != "POST":
        return redirect("client_rates", client_id=client.id)

    source = VehicleType.objects.filter(pk=request.POST.get("from_type") or None).first()
    targets = list(VehicleType.objects.filter(pk__in=request.POST.getlist("to_types")).exclude(pk=getattr(source, "pk", None)))
    if not source or not targets:
        messages.error(request, "Copy Rates: choose the vehicle type to copy FROM and at least one type to copy TO.")
        return redirect("client_rates", client_id=client.id)

    copied, skipped = copy_rates(client, source, targets)
    names = ", ".join(t.name for t in targets)
    if copied:
        messages.success(request, f"Copied {copied} rate(s) from {source.name} to {names}."
                         + (f" {skipped} already up to date, left as is." if skipped else ""))
    elif skipped:
        messages.info(request, f"Nothing to copy - {names} already has the latest {source.name} rates.")
    else:
        messages.warning(request, f"{source.name} has no rates for {client.name} to copy.")
    return redirect("client_rates", client_id=client.id)
