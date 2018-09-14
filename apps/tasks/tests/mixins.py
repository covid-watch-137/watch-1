import datetime

import factory

from .factories import (
    PatientTaskTemplateFactory,
    PatientTaskFactory,
    MedicationTaskTemplateFactory,
    MedicationTaskFactory,
)
from apps.plans.tests.mixins import PlansMixin


class TasksMixin(PlansMixin):

    def create_patient_task_template(self, plan_template=None):
        if plan_template is None:
            plan_template = self.create_care_plan_template()

        appear_time = datetime.time(8, 0, 0)
        due_time = datetime.time(17, 0, 0)
        return PatientTaskTemplateFactory(
            plan_template=plan_template,
            name=factory.Faker('name'),
            start_on_day=5,
            appear_time=appear_time,
            due_time=due_time,
        )

    def create_patient_task(self):
        plan = self.create_care_plan()
        patient_task_template = self.create_patient_task_template()
        appear_time = self.fake.future_datetime(end_date="+5d")
        due_datetime = self.fake.future_datetime(end_date="+30d")
        return PatientTaskFactory(
            plan=plan,
            patient_task_template=patient_task_template,
            appear_datetime=appear_time,
            due_datetime=due_datetime,
        )

    def create_medication_task_template(self):
        appear_time = datetime.time(8, 0, 0)
        due_time = datetime.time(17, 0, 0)
        return MedicationTaskTemplateFactory(
            plan=self.create_care_plan(),
            patient_medication=self.create_patient_medication(),
            start_on_day=5,
            appear_time=appear_time,
            due_time=due_time,
        )

    def create_medication_task(self):
        appear_datetime = self.fake.future_datetime(end_date="+5d")
        due_datetime = self.fake.future_datetime(end_date="+30d")
        return MedicationTaskFactory(
            medication_task_template=self.create_medication_task_template(),
            appear_datetime=appear_datetime,
            due_datetime=due_datetime,
        )
