# Generated by Django 5.0.6 on 2024-07-13 12:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_investment_sale_price"),
    ]

    operations = [
        migrations.AlterField(
            model_name="investment",
            name="sale_price",
            field=models.FloatField(blank=True, null=True),
        ),
    ]