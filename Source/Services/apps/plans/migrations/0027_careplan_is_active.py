# Generated by Django 2.0.7 on 2019-02-19 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0026_auto_20190218_1312'),
    ]

    operations = [
        migrations.AddField(
            model_name='careplan',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
