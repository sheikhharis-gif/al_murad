from django.db import models
from django.utils import timezone
from masters.models import Vehicle

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
    job_date = models.DateField(auto_now_add=True)
    completion_date = models.DateTimeField(null=True, blank=True) 
    
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

# -----------------------
# TRIP MODEL
# -----------------------
class Trip(models.Model):
    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name="trips")
    client = models.ForeignKey("masters.Client", on_delete=models.PROTECT, related_name="trips")
    
    # Yahan driver ki koi field nahi hai
    vehicle = models.ForeignKey("masters.Vehicle", on_delete=models.PROTECT, editable=False)
    trip_no = models.CharField(max_length=50, blank=True, editable=False)
    trip_date = models.DateField()
    route = models.ForeignKey("masters.Route", on_delete=models.PROTECT)
    
    bilty_number = models.CharField(max_length=50)
    weight = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=10, decimal_places=2)
    detention = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    freight = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        # Driver ka koi zikr nahi, sirf vehicle fetch ho raha hai
        self.vehicle = self.job.vehicle

        if not self.trip_no:
            count = Trip.objects.filter(job=self.job).count()
            self.trip_no = str(count + 1)

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Job {self.job.job_number} | Trip {self.trip_no}"

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

