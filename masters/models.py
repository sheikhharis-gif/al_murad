import re
from datetime import date, timedelta
from django.db import models

# ================= STAFF =================
class Staff(models.Model):
    employee_id = models.CharField("Employee ID", max_length=20, blank=True, editable=False)
    designation = models.CharField("Designation", max_length=100, blank=True)
    name = models.CharField("Full Name", max_length=100)
    father_name = models.CharField("Father Name", max_length=100)
    date_of_birth = models.DateField("Date of Birth", null=True, blank=True)
    address = models.TextField("Address")
    mobile1 = models.CharField("Mobile 1 #", max_length=20)
    mobile2 = models.CharField("Mobile 2 #", max_length=20, blank=True)
    cnic = models.CharField("CNIC #", max_length=15, unique=True)
    cnic_expiry = models.DateField("CNIC Expiry")
    license_number = models.CharField("License #", max_length=50, blank=True)
    license_category = models.CharField("License Category", max_length=50, blank=True)
    license_expiry = models.DateField("License Expiry", null=True, blank=True)
    salary = models.DecimalField("Salary", max_digits=12, decimal_places=2, null=True, blank=True)
    reference1_name = models.CharField("Primary Contact Name", max_length=100, blank=True)
    reference1_mobile = models.CharField("Primary Contact Number", max_length=20, blank=True)
    reference2_name = models.CharField("Secondary Contact Name", max_length=100, blank=True)
    reference2_mobile = models.CharField("Secondary Contact Number", max_length=20, blank=True)
    next_of_kin_name = models.CharField("Next of Kin Name", max_length=100, blank=True)
    next_of_kin_mobile = models.CharField("Next of Kin Number", max_length=20, blank=True)
    next_of_kin_relation = models.CharField("Next of Kin Relation", max_length=50, blank=True)
    joining_date = models.DateField("Joining Date")
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.employee_id:
            # Based on the highest existing number, not the row count, so a
            # deleted staff member in the middle can never cause a collision.
            max_num = 0
            for eid in Staff.objects.exclude(employee_id="").values_list("employee_id", flat=True):
                match = re.search(r"(\d+)$", eid)
                if match:
                    max_num = max(max_num, int(match.group(1)))
            self.employee_id = f"ALMRD-{max_num + 1:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]
# ================= SUPPLIER TYPE (admin-extensible registry) =================
class SupplierType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


# ================= VENDOR (displayed to users as "Supplier") =================
class Vendor(models.Model):
    name = models.CharField("Supplier Name", max_length=150)
    supplier_type = models.ForeignKey(
        SupplierType, on_delete=models.PROTECT, null=True, blank=True, related_name="vendors"
    )
    poc1_name = models.CharField("Point of Contact 1", max_length=100, blank=True)
    poc1_phone = models.CharField("Phone / Mobile Number", max_length=20, blank=True)
    poc1_email = models.EmailField("Email", blank=True)
    poc2_name = models.CharField("Point of Contact 2", max_length=100, blank=True)
    poc2_phone = models.CharField("Phone / Mobile Number", max_length=20, blank=True)
    poc2_email = models.EmailField("Email", blank=True)
    address = models.TextField(blank=True)
    ntn = models.CharField("NTN #", max_length=30, blank=True)
    stn = models.CharField("STN #", max_length=30, blank=True)
    term_of_service = models.CharField("Terms of Service", max_length=100, blank=True)
    billing_period = models.CharField("Billing Period", max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        for field in (
            "name", "poc1_name", "poc1_email", "poc2_name", "poc2_email",
            "address", "ntn", "stn", "term_of_service", "billing_period",
        ):
            value = getattr(self, field, None)
            if value:
                setattr(self, field, value.strip().upper())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ================= FUEL PRODUCT (admin-extensible registry) =================
class FuelProduct(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


# ================= VENDOR FUEL PRICE (only relevant for Supplier Type = FUEL) =================
class VendorFuelPrice(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name="fuel_prices")
    product = models.ForeignKey(FuelProduct, on_delete=models.PROTECT, related_name="vendor_prices")
    fuel_price = models.DecimalField("Fuel Price", max_digits=10, decimal_places=2)
    effective_date = models.DateField()

    class Meta:
        ordering = ["-effective_date", "-id"]

    def __str__(self):
        return f"{self.vendor} - {self.product} ({self.effective_date})"


# ================= VENDOR RATE =================
class VendorRate(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    route = models.ForeignKey("Route", on_delete=models.CASCADE)
    fuel_price = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()

    def __str__(self):
        return f"{self.vendor} - {self.route}"

# ================= VEHICLE =================
# ================= VEHICLE TYPE (admin-extensible registry) =================
class VehicleType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


# ================= WHEELER (admin-extensible registry) =================
class Wheeler(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Vehicle(models.Model):
    VEHICLE_MODE = [
        ("OWN", "Own"),
        ("RENTAL", "Rental"),
    ]

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("MAINTENANCE", "Under Maintenance"),
        ("IDLE", "Idle"),
        ("INACTIVE", "Inactive"),
    ]

    # ForeignKey to Vendor - optional; only relevant when vehicle_mode is Rental
    vendor = models.ForeignKey('Vendor', on_delete=models.PROTECT, null=True, blank=True, related_name='vehicles')

    # Dropdown ke liye Staff link (ForeignKey)
    # Isse aapko form mein staff ki list mil jayegi
    driver = models.ForeignKey(
        'Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles',
        help_text="Select staff member from the registered list"
    )
    driver2 = models.ForeignKey(
        'Staff',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='vehicles_as_second_driver',
        verbose_name="Second Driver",
        help_text="Optional second staff member assigned to this vehicle"
    )

    vehicle_mode = models.CharField(max_length=10, choices=VEHICLE_MODE, default="OWN")
    vehicle_number = models.CharField(max_length=20, unique=True)
    current_location = models.ForeignKey(
        'City', on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles_here'
    )
    vehicle_type = models.ForeignKey(VehicleType, on_delete=models.PROTECT, null=True, blank=True, related_name='vehicles')
    engine_no = models.CharField(max_length=50, blank=True, null=True)
    chassis_no = models.CharField(max_length=50, blank=True, null=True)
    container_no = models.CharField(max_length=50, blank=True, null=True)
    wheeler = models.ForeignKey(Wheeler, on_delete=models.PROTECT, null=True, blank=True, related_name='vehicles')
    fuel_type = models.ForeignKey(
        'FuelProduct', on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles'
    )
    color = models.CharField(max_length=30, blank=True)

    # Expiry Dates
    sindh_permit_expiry = models.DateField(null=True, blank=True)
    punjab_permit_expiry = models.DateField(null=True, blank=True)
    kpk_permit_expiry = models.DateField(null=True, blank=True)
    balochistan_permit_expiry = models.DateField(null=True, blank=True)
    fitness_expiry_sindh = models.DateField(null=True, blank=True)
    fitness_expiry_punjab = models.DateField(null=True, blank=True)
    fitness_expiry_kpk = models.DateField(null=True, blank=True)
    fitness_expiry_balochistan = models.DateField(null=True, blank=True)

    # Old text fields removed - Ab driver database se link hai

    is_active = models.BooleanField(default=True)
    starting_km = models.PositiveIntegerField("Starting KMs", default=0)
    current_km = models.PositiveIntegerField("Current KMs", default=0)

    # ===== Vehicle detail fields =====
    owner = models.CharField(max_length=150, blank=True)
    model_year = models.PositiveIntegerField("Model", null=True, blank=True)
    make = models.CharField(max_length=100, blank=True)
    weight_capacity = models.CharField("Weight Capacity", max_length=30, blank=True)
    purchase_date = models.DateField(null=True, blank=True)
    value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    leased = models.BooleanField(default=False)
    registration_name = models.CharField(max_length=150, blank=True)
    m_tag = models.CharField("M-Tag #", max_length=50, blank=True)
    dedicated_client = models.ForeignKey(
        'Client', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='dedicated_vehicles', verbose_name="Dedicated to Client"
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="ACTIVE")

    def save(self, *args, **kwargs):
        for field in ("vehicle_number", "engine_no", "chassis_no", "container_no", "color", "make", "registration_name", "m_tag", "owner", "weight_capacity"):
            value = getattr(self, field, None)
            if value:
                setattr(self, field, value.strip().upper())
        super().save(*args, **kwargs)

    # ===== SMART LOGIC FOR ALERTS =====
    def check_expiry(self, expiry_date):
        if not expiry_date:
            return 'none'
        today = date.today()
        warning_limit = today + timedelta(days=15)
        if expiry_date < today:
            return 'expired'
        elif today <= expiry_date <= warning_limit:
            return 'warning'
        return 'safe'

    @property
    def has_any_expiry_issue(self):
        dates = [
            self.sindh_permit_expiry, self.punjab_permit_expiry, 
            self.kpk_permit_expiry, self.balochistan_permit_expiry,
            self.fitness_expiry_sindh, self.fitness_expiry_punjab,
            self.fitness_expiry_kpk, self.fitness_expiry_balochistan
        ]
        for d in dates:
            if self.check_expiry(d) in ['expired', 'warning']:
                return True
        return False

    def __str__(self):
        return f"{self.vehicle_number} ({self.driver if self.driver else 'No Driver'})"


# ================= VEHICLE TYRES =================
class VehicleTyre(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="tyres")
    make = models.CharField("Tyre Make", max_length=100, blank=True)
    tyre_number = models.CharField(max_length=50)
    installed_date = models.DateField(null=True, blank=True)
    installed_km = models.PositiveIntegerField("Kilometer", null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def save(self, *args, **kwargs):
        self.tyre_number = (self.tyre_number or "").strip().upper()
        self.make = (self.make or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tyre_number} ({self.vehicle.vehicle_number})"


# ================= WORKSHOP: MAINTENANCE JOB =================
class MaintenanceJob(models.Model):
    MAINTENANCE_TYPES = [
        ("OIL", "Oil Change"),
        ("WHEEL", "Wheel Service"),
        ("BRAKE", "Brake Setting"),
        ("ELECTRICAL", "Electrical"),
        ("BODY", "Denting / Painting"),
        ("GENERAL", "General Service"),
        ("OTHER", "Other"),
    ]
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    ]
    PAYMENT_STATUS_CHOICES = [
        ("UNPAID", "Unpaid"),
        ("PAID", "Paid"),
    ]

    job_id = models.CharField(max_length=20, blank=True, editable=False, unique=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="maintenance_jobs")
    date = models.DateField()
    maintenance_type = models.CharField(max_length=15, choices=MAINTENANCE_TYPES, default="GENERAL")
    description = models.CharField(max_length=255, blank=True)

    odometer_km = models.PositiveIntegerField("Odometer (KM)", null=True, blank=True)
    next_service_due_km = models.PositiveIntegerField("Next Service Due (KM)", null=True, blank=True)

    spare_parts_vendor = models.CharField(max_length=100, blank=True)
    spare_parts_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    labor_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0, editable=False)

    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="PENDING")

    vendor_payment_status = models.CharField(
        "Vendor Payment Status", max_length=10, choices=PAYMENT_STATUS_CHOICES, default="UNPAID"
    )
    payment_date = models.DateField(null=True, blank=True)
    bill_ref = models.CharField("Payment Date / Bill Ref", max_length=50, blank=True)
    unpaid_balance = models.DecimalField("Unpaid Balance (PKR)", max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if not self.job_id:
            count = MaintenanceJob.objects.count()
            self.job_id = f"J{count + 1:03d}"
        self.total_cost = (self.spare_parts_cost or 0) + (self.labor_cost or 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job_id} - {self.vehicle.vehicle_number}"

    class Meta:
        ordering = ["-date", "-id"]


# ================= WORKSHOP: PARTS USED ON A JOB =================
class MaintenancePart(models.Model):
    SOURCE_CHOICES = [
        ("OWN", "Own Inventory"),
        ("VENDOR", "Direct Vendor Purchase"),
    ]

    job = models.ForeignKey(MaintenanceJob, on_delete=models.CASCADE, related_name="parts_used")
    part_used = models.CharField(max_length=150)
    quantity_used = models.PositiveIntegerField(default=1)
    part_source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default="OWN")
    inventory_item = models.ForeignKey(
        "PartsInventory", on_delete=models.SET_NULL, null=True, blank=True, related_name="usages",
        help_text="Link to a Parts Inventory row so 'Own Inventory' usage draws down its stock",
    )

    def __str__(self):
        return f"{self.part_used} x{self.quantity_used}"


# ================= WORKSHOP: PARTS INVENTORY =================
class PartsInventory(models.Model):
    CATEGORY_CHOICES = [
        ("GREASE", "Grease"),
        ("NUT_BOLT", "Nut Bolt"),
        ("FLUID", "Fluid"),
        ("SEAL", "Seal"),
        ("PIPE", "Pipe"),
        ("OTHER", "Other"),
    ]

    part_id = models.CharField(max_length=20, blank=True, editable=False, unique=True)
    part_name = models.CharField("Part Name", max_length=150)
    category = models.CharField(max_length=10, choices=CATEGORY_CHOICES, blank=True)
    stock_level = models.PositiveIntegerField("Stock Level", default=0)
    reorder_point = models.PositiveIntegerField("Reorder Point", default=0)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    total_used = models.PositiveIntegerField("Total Used", default=0, editable=False)
    remaining_stock = models.IntegerField("Remaining Stock", default=0, editable=False)

    def recalc_usage(self):
        used = self.usages.filter(part_source="OWN").aggregate(total=models.Sum("quantity_used"))["total"] or 0
        self.total_used = used
        self.remaining_stock = self.stock_level - used

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        if not self.part_id:
            count = PartsInventory.objects.count()
            self.part_id = f"P{count + 1:03d}"
        self.total_value = (self.stock_level or 0) * (self.unit_cost or 0)
        if is_new:
            # No MaintenancePart could reference this row before it has a pk.
            self.total_used = 0
            self.remaining_stock = self.stock_level
        else:
            self.recalc_usage()
        super().save(*args, **kwargs)

    @property
    def status(self):
        return "REORDER" if self.remaining_stock <= self.reorder_point else "GOOD"

    def __str__(self):
        return f"{self.part_id} - {self.part_name}"

    class Meta:
        verbose_name_plural = "Parts Inventory"
        ordering = ["part_name"]
# ================= CLIENT TYPE (admin-extensible registry) =================
class ClientType(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


# ================= CLIENT =================
class Client(models.Model):
    name = models.CharField(max_length=100)
    client_type = models.ForeignKey(
        ClientType, on_delete=models.PROTECT, null=True, blank=True, related_name="clients"
    )
    poc1_name = models.CharField("Point of Contact 1", max_length=100, blank=True)
    poc1_phone = models.CharField("Phone / Mobile Number", max_length=20, blank=True)
    poc1_email = models.EmailField("Email", blank=True)
    poc2_name = models.CharField("Point of Contact 2", max_length=100, blank=True)
    poc2_phone = models.CharField("Phone / Mobile Number", max_length=20, blank=True)
    poc2_email = models.EmailField("Email", blank=True)
    ntn = models.CharField("NTN #", max_length=20, unique=True)
    stn = models.CharField("STN #", max_length=30, blank=True)
    term_of_service = models.CharField("Terms of Service", max_length=100, blank=True)
    billing_period = models.CharField("Billing Period", max_length=50, blank=True)
    address = models.TextField()
    billing_company = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        for field in (
            "name", "poc1_name", "poc1_email", "poc2_name", "poc2_email",
            "address", "ntn", "stn", "term_of_service", "billing_period", "billing_company",
        ):
            value = getattr(self, field, None)
            if value:
                setattr(self, field, value.strip().upper())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# ================= CLIENT RATE =================
# Fuel-price-indexed rate revision log, one row per revision. For the first
# revision of a (client, route) pair, Current Fuel Price/Current Rate are
# typed in manually; every later revision auto-chains off the previous
# revision's Updated Fuel Price/Updated Trip Cost (client-side JS fills
# these in and locks them, mirroring "CLIENT RATE FILE.xlsx").
class ClientRate(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="rates")
    route = models.ForeignKey("Route", on_delete=models.CASCADE, related_name="client_rates")
    current_fuel_price = models.DecimalField("Current Fuel Price", max_digits=10, decimal_places=2)
    current_rate = models.DecimalField("Current Rate", max_digits=12, decimal_places=2)
    effective_percent = models.DecimalField("Effective %", max_digits=5, decimal_places=2)
    rate_subject_to_revision = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    updated_fuel_price = models.DecimalField("Updated Fuel Price", max_digits=10, decimal_places=2)
    fuel_price_change_percent = models.DecimalField(max_digits=6, decimal_places=2, editable=False)
    rate_adjustment = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    updated_trip_cost = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    weight_tons = models.DecimalField("Weight (Tons)", max_digits=8, decimal_places=2, null=True, blank=True)
    vehicle_type = models.ForeignKey(
        VehicleType, on_delete=models.SET_NULL, null=True, blank=True, related_name="client_rates"
    )
    effective_date = models.DateField()

    class Meta:
        ordering = ["route__route_code", "-effective_date", "-id"]

    def save(self, *args, **kwargs):
        self.rate_subject_to_revision = self.current_rate * (self.effective_percent / 100)
        self.fuel_price_change_percent = (
            (self.updated_fuel_price - self.current_fuel_price) / self.current_fuel_price * 100
            if self.current_fuel_price else 0
        )
        self.rate_adjustment = self.rate_subject_to_revision * (self.fuel_price_change_percent / 100)
        self.updated_trip_cost = self.current_rate + self.rate_adjustment
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client} - {self.route} ({self.effective_date})"


# ================= DEDICATED RATE =================
# The other "Mode" of Client Rates (alongside the Trip fuel-price revision
# log above): a per-vehicle monthly cost profile - a Fixed Cost/month plus
# a Variable Cost per KM derived from fuel price/average, matching
# "Dedicated.xlsx". Distance can come from the Route's registered distance
# (Standard), a future Job Orders KM tracker (Actual - not wired up yet, no
# real source exists for it today so it falls back to the Route distance
# too), or be typed by hand (Tracker).
class DedicatedRate(models.Model):
    DISTANCE_MODE_CHOICES = [
        ("STANDARD", "Standard (from Route)"),
        ("ACTUAL", "Actual (from Job Orders)"),
        ("TRACKER", "Tracker (manual)"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="dedicated_rates")
    vehicle = models.ForeignKey("Vehicle", on_delete=models.PROTECT, related_name="dedicated_rates")
    fixed_cost = models.DecimalField("Fixed Cost", max_digits=12, decimal_places=2)
    month = models.DateField("Month")
    fuel_avg = models.DecimalField("Fuel Avg (Km/Ltr)", max_digits=6, decimal_places=2)
    fuel_price = models.DecimalField("Fuel Price", max_digits=10, decimal_places=2)
    variable_cost = models.DecimalField("Variable Cost (Rs/Km)", max_digits=10, decimal_places=2, editable=False)
    route = models.ForeignKey("Route", on_delete=models.PROTECT, related_name="dedicated_rates")
    distance_mode = models.CharField(max_length=10, choices=DISTANCE_MODE_CHOICES, default="STANDARD")
    distance_km = models.DecimalField("Distance (Km)", max_digits=10, decimal_places=2)
    weight_tons = models.DecimalField("Weight (Tons)", max_digits=8, decimal_places=2, null=True, blank=True)
    vehicle_type = models.ForeignKey(
        VehicleType, on_delete=models.SET_NULL, null=True, blank=True, related_name="dedicated_rates"
    )
    effective_date = models.DateField()

    class Meta:
        ordering = ["route__route_code", "-effective_date", "-id"]

    def save(self, *args, **kwargs):
        self.variable_cost = (self.fuel_price / self.fuel_avg) if self.fuel_avg else 0
        if self.distance_mode in ("STANDARD", "ACTUAL") and self.route_id:
            self.distance_km = self.route.distance_km
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client} - {self.vehicle} ({self.effective_date})"



from django.db import models

# ================= EXPENSE (FIXED) =================
class Expense(models.Model):
    trip = models.ForeignKey(
        "operations.Trip",  
        on_delete=models.CASCADE,
        related_name="expenses"
    )

    date = models.DateField()
    slip_no = models.CharField(max_length=50, blank=True, null=True)

    # --- Fuel Details ---
    # fuel_liter hi kafi hai, 'total_diesel' alag se rakhne ki zaroorat nahi
    fuel_liter = models.FloatField(default=0, help_text="Total Liters filled")
    fuel_rate = models.FloatField(default=0, help_text="Rate per liter") # Naya: calculation ke liye
    fuel_amount = models.FloatField(default=0, help_text="Total fuel cost")
    pump_name = models.CharField(max_length=100, blank=True, null=True)

    # --- Other Trip Expenses ---
    toll_tax = models.FloatField(default=0)
    inam = models.FloatField(default=0)
    police = models.FloatField(default=0)
    food = models.FloatField(default=0)
    card = models.FloatField(default=0)
    maintenance = models.FloatField(default=0)
    other = models.FloatField(default=0)

    # Final Total (Fuel + All Other Expenses)
    total_expense = models.FloatField(default=0, editable=False)

    def save(self, *args, **kwargs):
        # Auto Calculate Fuel Amount agar rate diya ho (Optional)
        if self.fuel_liter and self.fuel_rate:
            self.fuel_amount = self.fuel_liter * self.fuel_rate
        
        # Auto Calculate Grand Total
        self.total_expense = (
            self.fuel_amount + self.toll_tax + self.inam + 
            self.police + self.food + self.card + 
            self.maintenance + self.other
        )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Expense for Trip #{self.trip.id} - {self.date}"


# ================= CITY =================
class City(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def save(self, *args, **kwargs):
        # All city entries are stored in CAPITALS.
        self.name = (self.name or "").strip().upper()
        self.code = (self.code or "").strip().upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        ordering = ["name"]


# ================= ROUTE =================
class Route(models.Model):
    origin = models.ForeignKey(City, on_delete=models.CASCADE, related_name="routes_from")
    destination = models.ForeignKey(City, on_delete=models.CASCADE, related_name="routes_to")
    distance_km = models.PositiveIntegerField("KMs")
    tt_hours = models.DecimalField("Transit Duration (Hours)", max_digits=5, decimal_places=1, null=True, blank=True)
    route_code = models.CharField(max_length=20, blank=True, editable=False)

    def save(self, *args, **kwargs):
        # Route code auto-merges from the two city codes, e.g. ISB-KHI.
        self.route_code = f"{self.origin.code}-{self.destination.code}".upper()
        super().save(*args, **kwargs)

    @property
    def transit_duration_display(self):
        # tt_hours is still stored/entered as a plain number of hours (e.g.
        # 50) - this just renders it as "2 Days 2 Hours" for display.
        if self.tt_hours is None:
            return None
        total_hours = float(self.tt_hours)
        days = int(total_hours // 24)
        hours = total_hours - (days * 24)
        hours = int(hours) if hours == int(hours) else round(hours, 1)
        parts = []
        if days:
            parts.append(f"{days} Day{'s' if days != 1 else ''}")
        if hours or not parts:
            parts.append(f"{hours} Hour{'s' if hours != 1 else ''}")
        return " ".join(parts)

    def __str__(self):
        return self.route_code.upper()

    class Meta:
        ordering = ["origin__name", "destination__name"]


# ================= DRIVER SALARY =================
class DriverSalary(models.Model):
    driver = models.ForeignKey(Staff, on_delete=models.CASCADE)
    month = models.DateField()

    emp_id = models.CharField("Emp ID", max_length=20, blank=True)
    designation = models.CharField(max_length=30, default="Driver")

    present_days = models.PositiveIntegerField(default=0)
    absent_days = models.PositiveIntegerField(default=0)
    sundays = models.PositiveIntegerField(default=0)

    base_salary = models.DecimalField("Base / Fixed Salary", max_digits=10, decimal_places=2, default=0)
    per_day_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    earned_base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    attendance_allowance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_gross_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    previous_advance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    new_advance_taken = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    advance_deduction = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    net_payable_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, default="Active")
    paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.driver} - {self.month}"


# ================= DRIVER ADVANCE =================
class DriverAdvance(models.Model):
    driver = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.driver} Advance {self.amount}"


# ================= STAFF MONTHLY ACCOUNT & EXPENSE STATEMENT =================
# One row per (staff, reporting month). The reporting month is locked to
# whichever month is currently open for that staff member - a new month can
# only be opened once the current one is closed (is_closed=True), and the
# closing balance of the last closed month becomes the next month's opening
# balance, so a due amount always carries forward.
class StaffMonthlyAccount(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name="monthly_accounts")
    month = models.DateField("Reporting Month")
    opening_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    is_closed = models.BooleanField(default=False)
    closed_date = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = ("staff", "month")
        ordering = ["-month"]

    def __str__(self):
        return f"{self.staff} - {self.month:%B %Y}"

    @property
    def total_present(self):
        return self.attendance.filter(status="PRESENT").count()

    @property
    def total_leave(self):
        return self.attendance.filter(status="LEAVE").count()

    @property
    def total_absent(self):
        return self.attendance.filter(status="ABSENT").count()

    @property
    def total_amount(self):
        return self.entries.aggregate(t=models.Sum("amount"))["t"] or 0

    @property
    def total_paid(self):
        return self.entries.aggregate(t=models.Sum("paid"))["t"] or 0

    @property
    def total_expense(self):
        return self.entries.aggregate(t=models.Sum("expense"))["t"] or 0

    @property
    def closing_balance(self):
        return (self.opening_balance or 0) + self.total_amount - self.total_paid - self.total_expense


# ================= STAFF ATTENDANCE SHEET (one row per day of the month) =================
class StaffAttendanceEntry(models.Model):
    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("LEAVE", "Leave"),
        ("ABSENT", "Absent"),
    ]
    account = models.ForeignKey(StaffMonthlyAccount, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="PRESENT")
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("account", "date")
        ordering = ["date"]

    def __str__(self):
        return f"{self.account} {self.date} {self.status}"


# ================= STAFF ACCOUNT (ledger entries: amount / paid / expense) =================
class StaffAccountEntry(models.Model):
    account = models.ForeignKey(StaffMonthlyAccount, on_delete=models.CASCADE, related_name="entries")
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expense = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["date", "id"]

    def __str__(self):
        return f"{self.account} {self.date}"
