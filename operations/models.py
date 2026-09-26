from django.db import models
from django.utils import timezone
from masters.models import Vehicle, VehicleType


def _format_duration(start, end):
    # "2 Days 2 Hours" - matches "job.xlsx"'s duration formulas.
    if not start or not end:
        return None
    delta = end - start
    total_seconds = delta.total_seconds()
    if total_seconds < 0:
        return None
    days = int(total_seconds // 86400)
    hours = int((total_seconds % 86400) // 3600)
    return f"{days} Days {hours} Hours"


# -----------------------
# JOB MODEL
# -----------------------
class Job(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress (On Road)'),
        ('returning', 'Returning'),
        ('completed', 'Completed (Back to Base)'),
        ('cancelled', 'Cancelled'),
    ]

    job_number = models.AutoField(primary_key=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='jobs')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    job_date = models.DateField(default=timezone.now)
    completion_date = models.DateTimeField(null=True, blank=True)

    trip_advance = models.DecimalField("Trip Advance", max_digits=12, decimal_places=2, default=0)
    remarks = models.TextField(blank=True, help_text="Voyage related notes")

    def __str__(self):
        return f"Job #{self.job_number} | {self.vehicle.vehicle_number}"

    def save(self, *args, **kwargs):
        if self.status == 'completed' and not self.completion_date:
            self.completion_date = timezone.now()
        super(Job, self).save(*args, **kwargs)

    class Meta:
        verbose_name = "Operational Job"
        verbose_name_plural = "Operational Jobs"

    # ---- display ----
    @property
    def job_code(self):
        return f"{self.job_number:05d}"

    # ---- auto/aggregate fields (mirrors "job.xlsx") ----
    @property
    def trips_ordered(self):
        return self.trips.order_by("id")

    @property
    def meter_out(self):
        first = self.trips_ordered.first()
        return first.departure_meter if first else None

    @property
    def meter_in(self):
        last = self.trips_ordered.last()
        return last.arrival_meter if last else None

    @property
    def running_kms(self):
        if self.meter_in is None or self.meter_out is None:
            return None
        return self.meter_in - self.meter_out

    @property
    def fuel_in_liters(self):
        return self.fuel_entries.aggregate(t=models.Sum("liters"))["t"] or 0

    @property
    def fuel_avg_km_ltr(self):
        liters = self.fuel_in_liters
        km = self.running_kms
        if not liters or km is None:
            return None
        return round(float(km) / float(liters), 2)

    @property
    def total_freight(self):
        return self.trips.aggregate(t=models.Sum("freight"))["t"] or 0

    @property
    def trip_expense(self):
        breakdown = getattr(self, "expense_breakdown", None)
        return breakdown.total if breakdown else 0

    @property
    def fuel_expense(self):
        return self.fuel_entries.aggregate(t=models.Sum("amount"))["t"] or 0

    @property
    def expense_total(self):
        return self.trip_expense

    @property
    def difference(self):
        return (self.trip_advance or 0) - self.expense_total

    @property
    def trip_profit(self):
        return self.total_freight - (self.trip_expense + self.fuel_expense)

    @property
    def tp_percent(self):
        if not self.total_freight:
            return None
        return round(float(self.trip_profit) / float(self.total_freight) * 100, 2)

    @property
    def per_km_cost(self):
        km = self.running_kms
        if not km:
            return None
        return round(float(self.trip_expense + self.fuel_expense) / float(km), 2)


# -----------------------
# TRIP MODEL
# -----------------------
class Trip(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="trips")
    client = models.ForeignKey("masters.Client", on_delete=models.PROTECT, related_name="trips")

    # Same vehicle as the parent Job throughout - meter chaining across trips
    # (Departure Meter -> Arrival Meter -> next trip's Departure Meter) only
    # makes sense for one continuous vehicle.
    vehicle = models.ForeignKey("masters.Vehicle", on_delete=models.PROTECT, editable=False)
    trip_no = models.CharField(max_length=50, blank=True, editable=False)
    trip_date = models.DateField()
    route = models.ForeignKey("masters.Route", on_delete=models.PROTECT, related_name="job_trips")

    # Optional unit of the client this trip is for (e.g. Five Star -> Assia /
    # Revo) - picks which set of Client Rates prices the trip.
    sub_category = models.ForeignKey(
        "masters.ClientSubCategory", on_delete=models.PROTECT, null=True, blank=True, related_name="trips",
        verbose_name="Sub-Category",
    )

    # Per-trip vehicle type - defaults to the job vehicle's type but can be
    # changed on the trip (drives the freight rate lookup below).
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT, null=True, blank=True, related_name="trips")
    bilty_number = models.CharField(max_length=50, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    departure_meter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    reached_at = models.DateTimeField("Reached Date & Time", null=True, blank=True)
    departed_at = models.DateTimeField("Departure Date & Time", null=True, blank=True)
    arrival_meter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    arrived_at = models.DateTimeField("Arrival Date & Time", null=True, blank=True)
    delivered_at = models.DateTimeField("Delivery Date & Time", null=True, blank=True)

    # Stop on the way (route is the main leg, e.g. KHI-LRK, stopover e.g. SKZ).
    # Charged separately from Additional Charges; both are part of freight.
    stopover_city = models.ForeignKey(
        "masters.City", on_delete=models.PROTECT, null=True, blank=True, related_name="stopover_trips",
        verbose_name="Stopover City",
    )
    stopover_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    additional_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.CharField(max_length=255, blank=True)
    freight = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.vehicle = self.job.vehicle
        if not self.vehicle_type_id:
            self.vehicle_type_id = self.vehicle.vehicle_type_id

        # Departure meter chains from the previous trip's arrival meter in
        # this same job, else the vehicle's current KM (first leg).
        previous = Trip.objects.filter(job=self.job).exclude(pk=self.pk).order_by("id").last()
        if previous and previous.arrival_meter is not None:
            self.departure_meter = previous.arrival_meter
        else:
            self.departure_meter = self.vehicle.current_km

        # Arrival meter = departure meter + this leg's route distance.
        if self.departure_meter is not None and self.route_id:
            self.arrival_meter = self.departure_meter + self.route.distance_km

        self.freight = self.compute_freight()

        super().save(*args, **kwargs)

        # Vehicle's odometer keeps advancing with each trip leg's computed
        # arrival meter - never regress it if this save recomputed an
        # earlier/stale leg after a later one already moved it forward.
        if self.arrival_meter is not None and self.arrival_meter > self.vehicle.current_km:
            self.vehicle.current_km = self.arrival_meter
            self.vehicle.save(update_fields=["current_km"])

        # Trip ID is globally unique and keeps counting up regardless of
        # vehicle, job or date - it simply mirrors this row's own serial pk.
        if not self.trip_no:
            self.trip_no = f"{self.pk:06d}"
            super().save(update_fields=["trip_no"])

    @property
    def standard_transit_display(self):
        return self.route.transit_duration_display if self.route_id else None

    @property
    def loading_duration_display(self):
        return _format_duration(self.reached_at, self.departed_at)

    @property
    def unloading_duration_display(self):
        return _format_duration(self.arrived_at, self.delivered_at)

    def compute_freight(self):
        """Freight = Updated Trip Cost of the Client Rate in force on the trip's
        date + Additional Charges. Must match vehicle type AND weight exactly -
        a rate for a different tonnage on the same route/vehicle type must
        never be substituted in, even if it's the only one on file."""
        rate = matching_trip_cost(self.client_id, self.route_id, self.vehicle_type_id, self.weight, self.trip_date,
                                  sub_category_id=self.sub_category_id)
        return (rate or 0) + (self.additional_charges or 0) + (self.stopover_charges or 0)

    @property
    def status_display(self):
        """Where the trip is now, from its date-times (a time still in the
        future doesn't count yet): At Loading -> Departed -> Arrived -> Delivered."""
        now = timezone.now()
        for when, label in ((self.delivered_at, "Delivered"), (self.arrived_at, "Arrived"),
                            (self.departed_at, "Departured"), (self.reached_at, "At Loading")):
            if when and when <= now:
                return label
        return ""

    @property
    def actual_transit_display(self):
        if not self.reached_at:
            return "Nil"
        end = self.delivered_at or timezone.now()
        return _format_duration(self.reached_at, end)

    def __str__(self):
        return f"Job {self.job.job_number} | Trip {self.trip_no}"


def matching_trip_cost(client_id, route_id, vehicle_type_id, weight, on_date=None, sub_category_id=None):
    """Updated Trip Cost of the Client Rate for this client + route + vehicle
    type + tonnage that was in force on `on_date` (the latest one effective on
    or before it), so revising a rate never re-prices older trips. A trip
    dated before the first rate on file uses that first rate. None if there's
    no rate at all.

    A trip with a sub-category (e.g. Revo) uses that sub-category's own rates;
    if it has none for this route/type/tonnage it falls back to the client's
    plain default rates (sub-category left blank)."""
    if not (client_id and route_id and vehicle_type_id):
        return None
    from masters.models import ClientRate
    for sub_id in ([sub_category_id, None] if sub_category_id else [None]):
        rates = ClientRate.objects.filter(
            client_id=client_id, route_id=route_id, vehicle_type_id=vehicle_type_id, weight_tons=weight,
            sub_category_id=sub_id,
        ).only("updated_trip_cost")
        rate = None
        if on_date:
            rate = rates.filter(effective_date__lte=on_date).order_by("-effective_date", "-id").first()
            if not rate:
                rate = rates.order_by("effective_date", "id").first()
        else:
            rate = rates.order_by("-effective_date", "-id").first()
        if rate:
            return rate.updated_trip_cost
    return None


def refresh_trip_freight(client_id, route_id, vehicle_type_id, weight, sub_category_id=None):
    """Re-price every trip a Client Rate applies to, after that rate is added,
    edited, deleted or copied - a trip's freight is otherwise only worked out
    when the trip itself is saved, so trips entered before their rate existed
    stayed at 0. Only the freight column is touched (not meters/odometer).
    Returns how many trips changed."""
    rate_on = {}  # (trip date, trip sub-category) -> rate in force that day
    changed = 0
    trips = Trip.objects.filter(client_id=client_id, route_id=route_id, vehicle_type_id=vehicle_type_id,
                                weight=weight)
    # A sub-category's rate only touches that sub-category's trips; a default
    # (no sub-category) rate can also be what its sub-category trips fall back to.
    if sub_category_id:
        trips = trips.filter(sub_category_id=sub_category_id)
    for trip in trips.only("id", "freight", "additional_charges", "stopover_charges", "trip_date", "sub_category_id"):
        key = (trip.trip_date, trip.sub_category_id)
        if key not in rate_on:
            rate_on[key] = matching_trip_cost(client_id, route_id, vehicle_type_id, weight, trip.trip_date,
                                              sub_category_id=trip.sub_category_id) or 0
        freight = rate_on[key] + (trip.additional_charges or 0) + (trip.stopover_charges or 0)
        if trip.freight != freight:
            Trip.objects.filter(pk=trip.pk).update(freight=freight)
            changed += 1
    return changed


# -----------------------
# JOB EXPENSE (single shared breakdown per Job)
# -----------------------
class JobExpense(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name="expense_breakdown")
    toll_plaza = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    food = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    incentive = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    mobile_expense = models.DecimalField("Mobile Expense", max_digits=10, decimal_places=2, default=0)
    challan = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tyre_expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    loading = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    offloading = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    weighbridge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    maintenance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_charges = models.DecimalField("Labor Charges", max_digits=10, decimal_places=2, default=0)
    fuel = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    other = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    remarks = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        self.total = sum([
            self.toll_plaza or 0, self.food or 0, self.incentive or 0, self.mobile_expense or 0,
            self.challan or 0, self.tyre_expense or 0, self.service or 0, self.loading or 0,
            self.offloading or 0, self.weighbridge or 0, self.maintenance or 0,
            self.labor_charges or 0, self.fuel or 0, self.other or 0,
        ])
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Expense breakdown - Job #{self.job.job_number}"


# -----------------------
# JOB FUEL ENTRY (multiple rows per Job)
# -----------------------
class JobFuelEntry(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="fuel_entries")
    supplier = models.ForeignKey("masters.Vendor", on_delete=models.PROTECT, related_name="job_fuel_entries")
    date = models.DateField()
    product = models.ForeignKey("masters.FuelProduct", on_delete=models.PROTECT, related_name="job_fuel_entries")
    slip_number = models.CharField("Slip #", max_length=50, blank=True)
    liters = models.DecimalField("Fuel in Liters", max_digits=10, decimal_places=2)
    fuel_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    class Meta:
        ordering = ["date", "id"]

    def save(self, *args, **kwargs):
        self.amount = (self.liters or 0) * (self.fuel_price or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.supplier} - {self.liters}L ({self.date})"


# -----------------------
# INVOICE MODEL
# -----------------------
class Invoice(models.Model):
    job = models.OneToOneField(Job, on_delete=models.CASCADE)
    invoice_date = models.DateField(auto_now_add=True)

    def total_amount(self):
        return sum(trip.freight for trip in self.job.trips.all())

    def __str__(self):
        return f"Invoice - Job #{self.job.job_number}"


# -----------------------
# GENERATED INVOICE (Reports > Generate Invoice) - a record of every invoice
# PDF produced there, so Invoices Status can list them and its status can be
# tracked. The PDF itself isn't stored - it's rebuilt on demand from the
# trips/columns/tax settings captured here, which is exactly what produced
# it originally.
# -----------------------
class GeneratedInvoice(models.Model):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("SENT", "Sent"),
        ("PAID", "Paid"),
        ("CANCELLED", "Cancelled"),
    ]
    TAX_MODE_CHOICES = [("FULL", "Full"), ("PARTIAL", "Partial")]

    invoice_no = models.CharField(max_length=30, unique=True, editable=False)
    client = models.ForeignKey("masters.Client", on_delete=models.PROTECT, related_name="generated_invoices")
    company = models.ForeignKey("masters.Company", on_delete=models.PROTECT, related_name="generated_invoices")
    trips = models.ManyToManyField(Trip, related_name="generated_invoices")
    columns = models.JSONField(default=list)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    payment_days = models.PositiveSmallIntegerField(default=30)
    notes = models.TextField(blank=True)
    # Shown in the invoice header's "SALES TAX no." slot; typed per invoice, blank by default.
    sales_tax_no = models.CharField(max_length=40, blank=True)

    tax_enabled = models.BooleanField(default=False)
    tax_mode = models.CharField(max_length=10, choices=TAX_MODE_CHOICES, blank=True)
    tax_rates = models.JSONField(default=dict, blank=True)

    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")

    class Meta:
        ordering = ["-created_at", "-id"]

    def save(self, *args, **kwargs):
        if not self.invoice_no:
            # e.g. SFS-INV-2026-09-001 - the running number restarts each
            # month. Based on the highest existing number, not the row count,
            # so a deleted invoice in the middle can never cause a collision.
            from zoneinfo import ZoneInfo
            from masters.models import TaxSettings
            today = timezone.now().astimezone(ZoneInfo("Asia/Karachi"))
            stem = f"{TaxSettings.current().invoice_prefix}-{today:%Y-%m}-"
            max_num = 0
            for no in GeneratedInvoice.objects.filter(invoice_no__startswith=stem).values_list("invoice_no", flat=True):
                tail = no[len(stem):]
                if tail.isdigit():
                    max_num = max(max_num, int(tail))
            self.invoice_no = f"{stem}{max_num + 1:03d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.invoice_no

