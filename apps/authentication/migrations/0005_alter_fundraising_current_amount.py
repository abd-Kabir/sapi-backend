# Generated by Django 5.2 on 2025-05-30 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0004_fundraising_donation_fundraising'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fundraising',
            name='current_amount',
            field=models.PositiveBigIntegerField(default=0),
        ),
    ]
