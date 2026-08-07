from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0025_dedicatedrate"),
    ]

    operations = [
        migrations.RenameModel(old_name="Driver", new_name="Staff"),
        migrations.RenameField(model_name="staff", old_name="mobile", new_name="mobile1"),
        migrations.AddField(
            model_name="staff",
            name="designation",
            field=models.CharField(blank=True, max_length=100, verbose_name="Designation"),
        ),
        migrations.AddField(
            model_name="staff",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True, verbose_name="Date of Birth"),
        ),
        migrations.AddField(
            model_name="staff",
            name="mobile2",
            field=models.CharField(blank=True, max_length=20, verbose_name="Mobile 2 #"),
        ),
        migrations.AddField(
            model_name="staff",
            name="license_category",
            field=models.CharField(blank=True, max_length=50, verbose_name="License Category"),
        ),
        migrations.AddField(
            model_name="staff",
            name="salary",
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Salary"),
        ),
        migrations.AddField(
            model_name="staff",
            name="next_of_kin_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="Next of Kin Name"),
        ),
        migrations.AddField(
            model_name="staff",
            name="next_of_kin_mobile",
            field=models.CharField(blank=True, max_length=20, verbose_name="Next of Kin Number"),
        ),
        migrations.AddField(
            model_name="staff",
            name="next_of_kin_relation",
            field=models.CharField(blank=True, max_length=50, verbose_name="Next of Kin Relation"),
        ),
        migrations.AlterField(
            model_name="staff",
            name="license_number",
            field=models.CharField(blank=True, max_length=50, verbose_name="License #"),
        ),
        migrations.AlterField(
            model_name="staff",
            name="license_expiry",
            field=models.DateField(blank=True, null=True, verbose_name="License Expiry"),
        ),
        migrations.AlterField(
            model_name="staff",
            name="name",
            field=models.CharField(max_length=100, verbose_name="Full Name"),
        ),
        migrations.AlterField(
            model_name="staff",
            name="reference1_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="Primary Contact Name"),
        ),
        migrations.AlterField(
            model_name="staff",
            name="reference1_mobile",
            field=models.CharField(blank=True, max_length=20, verbose_name="Primary Contact Number"),
        ),
        migrations.AlterField(
            model_name="staff",
            name="reference2_name",
            field=models.CharField(blank=True, max_length=100, verbose_name="Secondary Contact Name"),
        ),
        migrations.AlterField(
            model_name="staff",
            name="reference2_mobile",
            field=models.CharField(blank=True, max_length=20, verbose_name="Secondary Contact Number"),
        ),
        migrations.AlterField(
            model_name="staff",
            name="mobile1",
            field=models.CharField(max_length=20, verbose_name="Mobile 1 #"),
        ),
    ]
