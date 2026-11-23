from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("masters", "0053_client_manual_tonnage"),
    ]

    operations = [
        migrations.AddField(
            model_name="taxsettings",
            name="origin_city_rates",
            field=models.JSONField(blank=True, default=dict, verbose_name="Tax rates by origin city"),
        ),
    ]
