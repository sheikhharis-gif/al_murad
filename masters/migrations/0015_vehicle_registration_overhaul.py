import django.db.models.deletion
from django.db import migrations, models


# Old hardcoded Vehicle.VEHICLE_TYPES choice keys - every existing Vehicle row's
# vehicle_type value is one of these. Seeded into the new VehicleType registry
# (uppercased) so no vehicle silently loses its type during this migration.
VEHICLE_TYPE_LABELS = [
    "Mini Truck",
    "Suzuki Dry", "Suzuki Reefer",
    "Shahzore Dry", "Shahzore Reefer",
    "10ft Dry", "10ft Reefer",
    "14ft Dry", "14ft Reefer",
    "16ft Dry", "16ft Reefer",
    "17ft Dry", "17ft Reefer",
    "18ft Dry", "18ft Reefer",
    "20ft Dry", "20ft Reefer",
    "22ft Dry", "22ft Reefer",
    "24ft Dry", "24ft Reefer",
    "34ft Dry", "34ft Reefer",
    "40ft Dry", "40ft Reefer",
    "45ft Dry", "45ft Reefer",
    "50ft Dry", "50ft Reefer",
]

# Old hardcoded Vehicle.WHEELER choice keys -> their old display labels.
WHEELER_OLD_KEY_TO_LABEL = {
    "2x2": "2x2", "2x4": "2x4", "2x8": "2x8",
    "6x8": "6x8", "6x12": "6x12", "6x16": "6x16",
    "6": "6 Wheeler", "14": "14 Wheeler",
}


def seed_and_remap(apps, schema_editor):
    Vehicle = apps.get_model("masters", "Vehicle")
    VehicleType = apps.get_model("masters", "VehicleType")
    Wheeler = apps.get_model("masters", "Wheeler")
    City = apps.get_model("masters", "City")

    type_by_old_value = {}
    for label in VEHICLE_TYPE_LABELS:
        obj, _ = VehicleType.objects.get_or_create(name=label.strip().upper())
        type_by_old_value[label] = obj

    wheeler_by_old_value = {}
    for old_key, label in WHEELER_OLD_KEY_TO_LABEL.items():
        obj, _ = Wheeler.objects.get_or_create(name=label.strip().upper())
        wheeler_by_old_value[old_key] = obj

    unmatched_locations = 0
    for v in Vehicle.objects.all():
        changed = False

        old_type = v.vehicle_type_old
        if old_type:
            match = type_by_old_value.get(old_type)
            if not match:
                # Not one of the fixed choices (shouldn't normally happen) - register
                # it as-is rather than silently dropping the vehicle's type.
                match, _ = VehicleType.objects.get_or_create(name=old_type.strip().upper())
            v.vehicle_type_id = match.id
            changed = True

        old_wheeler = v.wheeler_old
        if old_wheeler:
            match = wheeler_by_old_value.get(old_wheeler)
            if not match:
                match, _ = Wheeler.objects.get_or_create(name=old_wheeler.strip().upper())
            v.wheeler_id = match.id
            changed = True

        old_location = v.current_location_old
        if old_location:
            city = City.objects.filter(name__iexact=old_location.strip()).first()
            if city:
                v.current_location_id = city.id
                changed = True
            else:
                unmatched_locations += 1

        if changed:
            v.save()

    if unmatched_locations:
        print(
            f"\n[vehicle migration] {unmatched_locations} vehicle(s) had a Current "
            "Location that isn't a registered city - left blank. Reassign it from "
            "the vehicle edit form once that city is registered.\n"
        )


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0014_route_tt_hours_alter_city_code_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="VehicleType",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Wheeler",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="VehicleTyre",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tyre_number", models.CharField(max_length=50)),
                ("installed_date", models.DateField(blank=True, null=True)),
                ("vehicle", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="tyres", to="masters.vehicle")),
            ],
        ),
        migrations.AddField(
            model_name="vehicle",
            name="leased",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="make",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="model_year",
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name="Model"),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="purchase_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="registration_name",
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="value",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True),
        ),
        migrations.AlterField(
            model_name="vehicle",
            name="vendor",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="vehicles", to="masters.vendor"),
        ),

        # --- Safe CharField -> ForeignKey conversion: rename the old text
        # columns out of the way, add the new FK columns under the final
        # names, populate them from the old values, then drop the old ones.
        migrations.RenameField(model_name="vehicle", old_name="vehicle_type", new_name="vehicle_type_old"),
        migrations.RenameField(model_name="vehicle", old_name="wheeler", new_name="wheeler_old"),
        migrations.RenameField(model_name="vehicle", old_name="current_location", new_name="current_location_old"),

        migrations.AddField(
            model_name="vehicle",
            name="vehicle_type",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vehicles", to="masters.vehicletype"),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="wheeler",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vehicles", to="masters.wheeler"),
        ),
        migrations.AddField(
            model_name="vehicle",
            name="current_location",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="vehicles_here", to="masters.city"),
        ),

        migrations.RunPython(seed_and_remap, reverse_noop),

        migrations.RemoveField(model_name="vehicle", name="vehicle_type_old"),
        migrations.RemoveField(model_name="vehicle", name="wheeler_old"),
        migrations.RemoveField(model_name="vehicle", name="current_location_old"),
    ]
