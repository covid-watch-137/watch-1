# Generated by Django 2.0.7 on 2019-06-04 12:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0068_assessmentquestion_assessment_template'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentquestion',
            name='assessment_task_template',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='tasks.AssessmentTaskTemplate'),
        ),
    ]