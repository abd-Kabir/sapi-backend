# Generated by Django 5.2 on 2025-06-27 20:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0022_notificationdistribution_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationdistribution',
            name='status',
            field=models.CharField(choices=[('waiting', 'Ожидается'), ('draft', 'Драфт'), ('sent', 'Отправлен')], default='waiting', max_length=55),
        ),
    ]
