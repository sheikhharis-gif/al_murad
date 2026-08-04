from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0023_vendor_is_active"),
    ]

    operations = [
        migrations.RemoveField(model_name="clientrate", name="rate"),
        migrations.RemoveField(model_name="clientrate", name="fuel_price"),
        migrations.AlterUniqueTogether(name="clientrate", unique_together=set()),
        migrations.AlterModelOptions(
            name="clientrate",
            options={"ordering": ["route__route_code", "-effective_date", "-id"]},
        ),
        migrations.AlterField(
            model_name="clientrate",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="rates", to="masters.client"
            ),
        ),
        migrations.AlterField(
            model_name="clientrate",
            name="route",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="client_rates", to="masters.route"
            ),
        ),
        migrations.AddField(
            model_name="clientrate",
            name="current_fuel_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10, verbose_name="Current Fuel Price"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="clientrate",
            name="current_rate",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=12, verbose_name="Current Rate"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="clientrate",
            name="effective_percent",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=5, verbose_name="Effective %"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="clientrate",
            name="rate_subject_to_revision",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), editable=False, max_digits=12),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="clientrate",
            name="updated_fuel_price",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), max_digits=10, verbose_name="Updated Fuel Price"),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="clientrate",
            name="fuel_price_change_percent",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), editable=False, max_digits=6),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="clientrate",
            name="rate_adjustment",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), editable=False, max_digits=12),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="clientrate",
            name="updated_trip_cost",
            field=models.DecimalField(decimal_places=2, default=Decimal("0"), editable=False, max_digits=12),
            preserve_default=False,
        ),
    ]
