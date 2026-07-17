from datetime import date, timedelta
from django.db import models

# ================= DRIVER =================
class Driver(models.Model):
    employee_id = models.CharField("Employee ID", max_length=20, blank=True, editable=False)
    name = models.CharField("Driver Name", max_length=100)
    father_name = models.CharField("Father Name", max_length=100)
    address = models.TextField("Address")
    mobile = models.CharField("Mobile #", max_length=20)
    cnic = models.CharField("CNIC #", max_length=15, unique=True)
    cnic_expiry = models.DateField("CNIC Expiry")
    license_number = models.CharField("License Number", max_length=50)
    license_expiry = models.DateField("License Expiry")
    reference1_name = models.CharField(max_length=100, blank=True)
    reference1_mobile = models.CharField(max_length=20, blank=True)
    reference2_name = models.CharField(max_length=100, blank=True)
    reference2_mobile = models.CharField(max_length=20, blank=True)
    joining_date = models.DateField("Joining Date")
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.employee_id:
            count = Driver.objects.exclude(employee_id="").count()
            self.employee_id = f"ALMRD-{count + 1:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
# ================= VENDOR =================
class Vendor(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20) # Yeh field template ke liye zaroori hai
    poc = models.CharField(max_length=100)
    ntn = models.CharField(max_length=20, blank=True)
    address = models.TextField()

    def __str__(self):
        return self.name


# ================= VENDOR RATE =================
class VendorRate(models.Model):
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE)
    route = models.ForeignKey("Route", on_delete=models.CASCADE)
    fuel_price = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()

    def __str__(self):
        return f"{self.vendor} - {self.route}"

# ================= VEHICLE =================
class Vehicle(models.Model):
    VEHICLE_MODE = [
        ("OWN", "Own"),
        ("RENTAL", "Rental"),
        ("FIXED", "Fixed"),
    ]
    
    VEHICLE_TYPES = [
        ("Mini Truck", "Mini Truck"),
        ("Suzuki Dry", "Suzuki Dry"), ("Suzuki Reefer", "Suzuki Reefer"),
        ("Shahzore Dry", "Shahzore Dry"), ("Shahzore Reefer", "Shahzore Reefer"),
        ("10ft Dry", "10ft Dry"), ("10ft Reefer", "10ft Reefer"),
        ("14ft Dry", "14ft Dry"), ("14ft Reefer", "14ft Reefer"),
        ("16ft Dry", "16ft Dry"), ("16ft Reefer", "16ft Reefer"),
        ("17ft Dry", "17ft Dry"), ("17ft Reefer", "17ft Reefer"),
        ("18ft Dry", "18ft Dry"), ("18ft Reefer", "18ft Reefer"),
        ("20ft Dry", "20ft Dry"), ("20ft Reefer", "20ft Reefer"),
        ("22ft Dry", "22ft Dry"), ("22ft Reefer", "22ft Reefer"),
        ("24ft Dry", "24ft Dry"), ("24ft Reefer", "24ft Reefer"),
        ("34ft Dry", "34ft Dry"), ("34ft Reefer", "34ft Reefer"),
        ("40ft Dry", "40ft Dry"), ("40ft Reefer", "40ft Reefer"),
        ("45ft Dry", "45ft Dry"), ("45ft Reefer", "45ft Reefer"),
        ("50ft Dry", "50ft Dry"), ("50ft Reefer", "50ft Reefer"),
    ]

    WHEELER = [
        ("2x2", "2x2"), ("2x4", "2x4"), ("2x8", "2x8"),
        ("6x8", "6x8"), ("6x12", "6x12"), ("6x16", "6x16"),
        ("6", "6 Wheeler"), ("14", "14 Wheeler"),
    ]

    # ForeignKey to Vendor
    vendor = models.ForeignKey('Vendor', on_delete=models.PROTECT, related_name='vehicles')
    
    # Dropdown ke liye Driver link (ForeignKey)
    # Isse aapko form mein driver ki list mil jayegi
    driver = models.ForeignKey(
        'Driver', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='vehicles',
        help_text="Select driver from the registered list"
    )

    vehicle_mode = models.CharField(max_length=10, choices=VEHICLE_MODE)
    vehicle_number = models.CharField(max_length=20, unique=True)
    current_location = models.CharField(max_length=100, default="Karachi", blank=True)     
    vehicle_type = models.CharField(max_length=30, choices=VEHICLE_TYPES)
    engine_no = models.CharField(max_length=50, blank=True, null=True)
    chassis_no = models.CharField(max_length=50, blank=True, null=True)
    container_no = models.CharField(max_length=50, blank=True, null=True)
    wheeler = models.CharField(max_length=10, choices=WHEELER)
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
    current_km = models.PositiveIntegerField(default=0)
    last_meter_update = models.DateField(null=True, blank=True)

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

# ================= VEHICLE MAINTENANCE (UPDATED WITH ALERTS) =================
class VehicleMaintenance(models.Model):

    MAINTENANCE_TYPE = [
        ("OIL", "Oil Change"),
        ("TIRE", "Tire Change"),
        ("BRAKE", "Brake Repair"),
        ("OTHER", "General Service"),
    ]

    # KM LIMITS (AUTO LOGIC)
    MAINTENANCE_LIMIT = {
        "OIL": 1000,    # Oil change after 1000 km
        "TIRE": 5000,   # Tire change after 5000 km
        "BRAKE": 10000, # Brake repair after 10000 km
        "OTHER": 3000,  # General service after 3000 km
    }

    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE)
    maintenance_type = models.CharField(max_length=10, choices=MAINTENANCE_TYPE)

    change_date = models.DateField()
    change_km = models.PositiveIntegerField()

    next_due_km = models.PositiveIntegerField(editable=False)
    next_due_date = models.DateField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        # Calculation logic (Fixed for types)
        limit = self.MAINTENANCE_LIMIT[self.maintenance_type]
        self.next_due_km = int(self.change_km) + int(limit)
        super().save(*args, **kwargs)

    def is_overdue(self):
        """Check if vehicle has crossed KM limit"""
        return self.vehicle.current_km >= self.next_due_km

    def get_status(self):
        """
        Custom logic for Dashboard Alerts:
        - OVERDUE (Red/Pulse): KM cross ho chuke hain ya Date guzar gayi hai.
        - CRITICAL (Red): 7 din ya 100 KM reh gaye hain.
        - WARNING (Yellow): 30 din reh gaye hain.
        """
        from datetime import date, timedelta
        today = date.today()
        
        # 1. OVERDUE (Sabse Khatarnak - Red Alert)
        if self.is_overdue() or (self.next_due_date and today > self.next_due_date):
            return "OVERDUE"
        
        # 2. CRITICAL (1 Week left - Red Alert)
        if self.next_due_date and today >= (self.next_due_date - timedelta(days=7)):
            return "CRITICAL"
            
        # 3. WARNING (1 Month left - Yellow Alert)
        if self.next_due_date and today >= (self.next_due_date - timedelta(days=30)):
            return "WARNING"
            
        return "HEALTHY"

    def __str__(self):
        return f"{self.vehicle.vehicle_number} - {self.maintenance_type}"	
# ================= CLIENT =================
class Client(models.Model):
    name = models.CharField(max_length=100)
    poc = models.CharField(max_length=100)
    ntn = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    billing_company = models.CharField(max_length=150, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# ================= CLIENT RATE =================
class ClientRate(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    route = models.ForeignKey("Route", on_delete=models.CASCADE)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    fuel_price = models.DecimalField(max_digits=10, decimal_places=2)
    effective_date = models.DateField()

    class Meta:
        unique_together = ("client", "route")

    def __str__(self):
        return f"{self.client} - {self.route}"





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
    code = models.CharField(max_length=10, unique=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)

    def __str__(self):
        return f"{self.name} ({self.code})"


# ================= ROUTE =================
class Route(models.Model):
    origin = models.ForeignKey(City, on_delete=models.CASCADE, related_name="routes_from")
    destination = models.ForeignKey(City, on_delete=models.CASCADE, related_name="routes_to")
    distance_km = models.PositiveIntegerField()
    route_code = models.CharField(max_length=20, blank=True)

    def save(self, *args, **kwargs):
        self.route_code = f"{self.origin.code}-{self.destination.code}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.route_code


# ================= DRIVER SALARY =================
class DriverSalary(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
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
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"{self.driver} Advance {self.amount}"
