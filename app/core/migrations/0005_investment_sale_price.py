# Generated by Django 5.0.6 on 2024-07-13 11:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_investment"),
    ]

    operations = [
        migrations.AddField(
            model_name="investment",
            name="sale_price",
            field=models.FloatField(blank=True, default=None),
            preserve_default=False,
        ),
    ]