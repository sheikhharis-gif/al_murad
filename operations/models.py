from django.db import models
from django.utils import timezone
from masters.models import Vehicle


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

    bilty_number = models.CharField(max_length=50, blank=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    departure_meter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    reached_at = models.DateTimeField("Reached Date & Time", null=True, blank=True)
    departed_at = models.DateTimeField("Departure Date & Time", null=True, blank=True)
    arrival_meter = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)
    arrived_at = models.DateTimeField("Arrival Date & Time", null=True, blank=True)
    delivered_at = models.DateTimeField("Delivery Date & Time", null=True, blank=True)

    additional_charges = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    remarks = models.CharField(max_length=255, blank=True)
    freight = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)

    class Meta:
        ordering = ["id"]

    def save(self, *args, **kwargs):
        self.vehicle = self.job.vehicle

        if not self.trip_no:
            count = Trip.objects.filter(job=self.job).count()
            self.trip_no = f"{count + 1:06d}"

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

        # Freight = latest matching Client Rate's Updated Trip Cost + Additional Charges.
        from masters.models import ClientRate
        rate_qs = ClientRate.objects.filter(client=self.client, route=self.route)
        matched = None
        if self.vehicle.vehicle_type_id:
            matched = rate_qs.filter(vehicle_type=self.vehicle.vehicle_type).order_by("-effective_date", "-id").first()
        if not matched:
            matched = rate_qs.order_by("-effective_date", "-id").first()
        base_freight = matched.updated_trip_cost if matched else 0
        self.freight = base_freight + (self.additional_charges or 0)

        super().save(*args, **kwargs)

    @property
    def standard_transit_display(self):
        return self.route.transit_duration_display if self.route_id else None

    @property
    def loading_duration_display(self):
        return _format_duration(self.reached_at, self.departed_at)

    @property
    def unloading_duration_display(self):
        return _format_duration(self.arrived_at, self.delivered_at)

    @property
    def actual_transit_display(self):
        if not self.reached_at:
            return "Nil"
        end = self.delivered_at or timezone.now()
        return _format_duration(self.reached_at, end)

    def __str__(self):
        return f"Job {self.job.job_number} | Trip {self.trip_no}"


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

