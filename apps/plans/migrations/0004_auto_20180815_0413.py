# Generated by Django 2.0.7 on 2018-08-15 10:13

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('plans', '0003_auto_20180815_0406'),
    ]

    operations = [
        migrations.AddField(
            model_name='messagestream',
            name='type',
            field=models.CharField(choices=[('education', 'Education'), ('support', 'Support'), ('medication', 'Medication')], default='education', max_length=40),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='streammessage',
            name='stream',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='plans.MessageStream'),
        ),
    ]
