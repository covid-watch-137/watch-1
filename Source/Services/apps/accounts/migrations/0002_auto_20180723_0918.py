# Generated by Django 2.0.7 on 2018-07-23 15:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='emailuser',
            options={'ordering': ('first_name', 'last_name'), 'verbose_name': 'user', 'verbose_name_plural': 'users'},
        ),
    ]
