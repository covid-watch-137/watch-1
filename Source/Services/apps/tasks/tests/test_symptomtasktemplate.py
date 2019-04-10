import datetime
import random

from django.urls import reverse
from django.utils import timezone

from dateutil.relativedelta import relativedelta
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from .mixins import TasksMixin
from apps.tasks.models import SymptomTaskTemplate


class TestSymptomTaskTemmplateUsingEmployee(TasksMixin, APITestCase):
    """
    Test cases for :model:`tasks.SymptomTaskTemmplate` using an employee
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.template = self.create_symptom_task_template()

        self.url = reverse('symptom_task_templates-list')
        self.detail_url = reverse(
            'symptom_task_templates-detail',
            kwargs={'pk': self.template.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_symptom_task_templates_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 1)

    def test_get_symptom_task_template_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_symptom_task_template_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_symptom_task_template(self):
        template = self.create_care_plan_template()
        symptom = self.create_symptom()

        payload = {
            'plan_template': template.id,
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
            'appear_time': datetime.time(8, 0, 0),
            'due_time': datetime.time(17, 0, 0),
            'default_symptoms': [symptom.id]
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_symptom_task_template_with_ongoing_plans(self):
        template = self.create_care_plan_template(duration_weeks=6)
        symptom = self.create_symptom()

        for i in range(3):
            plan = self.create_care_plan(
                plan_template=template
            )
            plan.created = timezone.now() - relativedelta(weeks=2)
            plan.save(update_fields=['created'])

        payload = {
            'plan_template': template.id,
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
            'appear_time': datetime.time(8, 0, 0),
            'due_time': datetime.time(17, 0, 0),
            'default_symptoms': [symptom.id]
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        task_template = SymptomTaskTemplate.objects.get(id=response.data['id'])
        self.assertTrue(task_template.symptom_tasks.exists())

    def test_create_symptom_task_template_with_ongoing_plans_weekly(self):
        total_duration = 6
        past_duration = 2
        plans_count = 3
        template = self.create_care_plan_template(
            duration_weeks=total_duration
        )
        symptom = self.create_symptom()

        for i in range(plans_count):
            plan = self.create_care_plan(
                plan_template=template
            )
            plan.created = timezone.now() - relativedelta(weeks=past_duration)
            plan.save(update_fields=['created'])

        payload = {
            'plan_template': template.id,
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
            'frequency': 'weekly',
            'appear_time': datetime.time(8, 0, 0),
            'due_time': datetime.time(17, 0, 0),
            'default_symptoms': [symptom.id]
        }
        response = self.client.post(self.url, payload)
        task_template = SymptomTaskTemplate.objects.get(id=response.data['id'])
        self.assertEqual(
            task_template.symptom_tasks.count(),
            (total_duration - past_duration) * plans_count
        )

    def test_full_update_symptom_task_template(self):
        template = self.create_care_plan_template()
        symptom = self.create_symptom()

        payload = {
            'plan_template': template.id,
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
            'appear_time': datetime.time(8, 0, 0),
            'due_time': datetime.time(17, 0, 0),
            'default_symptoms': [symptom.id]
        }
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_symptom_task_template(self):
        payload = {
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_symptom_task_template(self):
        now = timezone.now()
        plan = self.create_care_plan()
        tasks_before = 3
        tasks_after = 5

        for i in range(tasks_before):
            days_ago = 3 - i
            self.create_symptom_task(
                plan=plan,
                symptom_task_template=self.template,
                due_datetime=now - relativedelta(days=days_ago)
            )

        for i in range(tasks_after):
            self.create_symptom_task(
                plan=plan,
                symptom_task_template=self.template,
                due_datetime=now + relativedelta(days=i, hours=1)
            )

        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.template.symptom_tasks.count(), tasks_before)

        get_response = self.client.get(self.detail_url)
        self.assertFalse(get_response.data['is_active'])


class TestSymptomTaskTemmplateUsingPatient(TasksMixin, APITestCase):
    """
    Test cases for :model:`tasks.SymptomTaskTemmplate` using a patient
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.patient = self.create_patient()
        self.user = self.patient.user

        self.template = self.create_symptom_task_template()

        self.url = reverse('symptom_task_templates-list')
        self.detail_url = reverse(
            'symptom_task_templates-detail',
            kwargs={'pk': self.template.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_symptom_task_templates_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 1)

    def test_get_symptom_task_template_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_symptom_task_template_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_symptom_task_template(self):
        template = self.create_care_plan_template()

        payload = {
            'plan_template': template.id,
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
            'appear_time': datetime.time(8, 0, 0),
            'due_time': datetime.time(17, 0, 0)
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_update_symptom_task_template(self):
        template = self.create_care_plan_template()

        payload = {
            'plan_template': template.id,
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
            'appear_time': datetime.time(8, 0, 0),
            'due_time': datetime.time(17, 0, 0)
        }
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_symptom_task_template(self):
        payload = {
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_symptom_task_template(self):
        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
