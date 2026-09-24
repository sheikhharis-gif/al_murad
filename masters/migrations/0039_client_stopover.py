from django.db import migrations, models
import django.db.models.deletion


def assign_to_five_star(apps, schema_editor):
    """The stopover rates seeded earlier were Five Star's - give them to that
    client (and switch its Has Stopover Charges on); orphans are dropped."""
    Client = apps.get_model("masters", "Client")
    StopoverRate = apps.get_model("masters", "StopoverRate")
    five_star = Client.objects.filter(name__iexact="Five Star 3PL SERVICES").first()
    if five_star:
        StopoverRate.objects.update(client=five_star)
        Client.objects.filter(pk=five_star.pk).update(has_stopover=True)
    else:
        StopoverRate.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0038_stopover"),
    ]

    operations = [
        migrations.AddField(
            model_name="client",
            name="has_stopover",
            field=models.BooleanField(default=False, verbose_name="Has Stopover Charges"),
        ),
        migrations.RemoveConstraint(model_name="stopoverrate", name="uniq_stopover_rate_type_zone"),
        migrations.AddField(
            model_name="stopoverrate",
            name="client",
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name="stopover_rates", to="masters.client",
            ),
        ),
        migrations.RunPython(assign_to_five_star, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="stopoverrate",
            name="client",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stopover_rates", to="masters.client",
            ),
        ),
        migrations.AddConstraint(
            model_name="stopoverrate",
            constraint=models.UniqueConstraint(
                fields=("client", "vehicle_type", "zone"), name="uniq_stopover_rate_client_type_zone",
            ),
        ),
    ]
