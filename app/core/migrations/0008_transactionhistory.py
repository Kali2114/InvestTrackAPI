# Generated by Django 5.0.6 on 2024-07-13 14:04

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_remove_investment_updated_at_investment_sale_date"),
    ]

    operations = [
        migrations.CreateModel(
            name="TransactionHistory",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "transaction_id",
                    models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
                ),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[("sell", "Sell"), ("buy", "Buy")], max_length=10
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("stock", "Stock"),
                            ("bond", "Bond"),
                            ("cc", "Cryptocurrency"),
                        ],
                        max_length=255,
                    ),
                ),
                ("quantity", models.FloatField()),
                ("purchase_price", models.FloatField()),
                ("sale_price", models.FloatField()),
                ("purchase_date", models.DateTimeField()),
                ("sale_date", models.DateTimeField(auto_now_add=True)),
                (
                    "investment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.investment",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
