# Generated by Django 5.2 on 2025-07-13 16:52

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0028_alter_user_donation_banner'),
        ('files', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='donation_banner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='donation_banner', to='files.file'),
        ),
    ]
