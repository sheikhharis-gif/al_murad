from django.db import migrations


def rename(apps, schema_editor):
    ClientSubCategory = apps.get_model("masters", "ClientSubCategory")
    ClientSubCategory.objects.filter(name="ASSIA").update(name="ASAIA")


def unrename(apps, schema_editor):
    ClientSubCategory = apps.get_model("masters", "ClientSubCategory")
    ClientSubCategory.objects.filter(name="ASAIA").update(name="ASSIA")


class Migration(migrations.Migration):

    dependencies = [
        ("masters", "0039_client_stopover"),
    ]

    operations = [
        migrations.RunPython(rename, unrename),
    ]
