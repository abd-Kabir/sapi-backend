# Generated by Django 5.2 on 2025-06-25 15:27

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content', '0002_report_status'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='is_blocked',
            field=models.BooleanField(default=False),
        ),
        migrations.CreateModel(
            name='ReportComment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('text', models.TextField()),
                ('report', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_comments', to='content.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='report_comments', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'report_comment',
                'ordering': ['-created_at'],
            },
        ),
    ]
