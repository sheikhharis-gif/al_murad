from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("operations", "0014_invoice_recipient_client"),
    ]

    operations = [
        migrations.RenameField(model_name="generatedinvoice", old_name="company", new_name="provider_company"),
        migrations.RenameField(model_name="generatedinvoice", old_name="recipient_client", new_name="provider_client"),
    ]
