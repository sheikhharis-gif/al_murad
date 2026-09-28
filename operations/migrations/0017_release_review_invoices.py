from django.db import migrations


def cancel_draft_invoices(apps, schema_editor):
    """Before this release every PDF/Excel download created an invoice record, so the existing
    Draft ones are review copies. Cancel them so their trips aren't locked as Invoiced."""
    GeneratedInvoice = apps.get_model("operations", "GeneratedInvoice")
    GeneratedInvoice.objects.filter(status="DRAFT").update(status="CANCELLED")


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0016_remove_provider_client"),
    ]

    operations = [
        migrations.RunPython(cancel_draft_invoices, migrations.RunPython.noop),
    ]
