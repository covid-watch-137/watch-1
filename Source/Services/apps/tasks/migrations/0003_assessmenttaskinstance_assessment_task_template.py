# Generated by Django 2.0.7 on 2018-09-11 00:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0002_auto_20180910_1849'),
    ]

    operations = [
        migrations.AddField(
            model_name='assessmenttaskinstance',
            name='assessment_task_template',
            field=models.ForeignKey(default='fc69b06c-0f3b-43fe-a873-ea699dee7fdd', on_delete=django.db.models.deletion.CASCADE, to='tasks.AssessmentTaskTemplate'),
            preserve_default=False,
        ),
    ]