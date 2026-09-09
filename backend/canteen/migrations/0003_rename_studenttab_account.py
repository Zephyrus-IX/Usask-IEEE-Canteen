# Generated manually to preserve existing student tab data while renaming concepts.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("canteen", "0002_inventoryadjustment_restockevent_restockitem_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name="StudentTab",
            new_name="Account",
        ),
        migrations.RenameField(
            model_name="sale",
            old_name="student_tab",
            new_name="account",
        ),
        migrations.RenameField(
            model_name="balancetransaction",
            old_name="student_tab",
            new_name="account",
        ),
        migrations.AlterField(
            model_name="account",
            name="created_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="created_accounts",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="account",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="canteen_account",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
