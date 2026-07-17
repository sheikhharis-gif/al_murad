from django.core.management.base import BaseCommand

from masters.models import Client, Driver, DriverSalary, Vehicle
from operations.models import Job, Trip


class Command(BaseCommand):
    help = (
        "One-time cleanup: removes the placeholder/junk records created by earlier "
        "import commands (AMG.xlsx client-name-only rows and its 2 real trips/jobs, "
        "plus the TEST-EMP placeholder drivers and their salary rows from the salary "
        "sheet import), then backfills Employee ID for any driver missing one. "
        "Safe to re-run - matches nothing on a second run."
    )

    def handle(self, *args, **options):
        amg_jobs = Job.objects.filter(remarks__startswith="Imported Job from sheet row")
        amg_job_ids = list(amg_jobs.values_list("job_number", flat=True))
        amg_vehicle_ids = list(amg_jobs.values_list("vehicle_id", flat=True).distinct())

        trips_deleted = Trip.objects.filter(job__in=amg_job_ids).delete()[0]
        jobs_deleted = amg_jobs.delete()[0]

        vehicles_deleted = 0
        for vid in amg_vehicle_ids:
            v = Vehicle.objects.filter(id=vid).first()
            if v and v.jobs.count() == 0:
                v.delete()
                vehicles_deleted += 1

        clients_deleted = Client.objects.filter(poc="Imported POC").delete()[0]

        salary_count_before = DriverSalary.objects.filter(driver__cnic__startswith="TEST-EMP").count()
        drivers_deleted = Driver.objects.filter(cnic__startswith="TEST-EMP").delete()[0]

        backfilled = 0
        for d in Driver.objects.filter(employee_id="").order_by("id"):
            d.save()
            backfilled += 1

        self.stdout.write(self.style.SUCCESS(
            f"Deleted: {trips_deleted} AMG.xlsx trips, {jobs_deleted} jobs, "
            f"{vehicles_deleted} now-orphaned vehicle(s), {clients_deleted} client-only rows, "
            f"{drivers_deleted} TEST-EMP drivers ({salary_count_before} linked salary rows cascaded). "
            f"Backfilled Employee ID for {backfilled} driver(s)."
        ))
