import datetime
import random

from django.urls import reverse
from django.utils import timezone

from dateutil.relativedelta import relativedelta
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from .mixins import TasksMixin


class TestAssessmentTaskTemplateUsingEmployee(TasksMixin, APITestCase):
    """
    Test cases for :model:`tasks.AssessmentTaskTemplate` using an employee
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.template = self.create_assessment_task_template()

        self.create_multiple_assessment_questions(self.template)

        self.url = reverse('assessment_task_templates-list')
        self.detail_url = reverse(
            'assessment_task_templates-detail',
            kwargs={'pk': self.template.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_assessment_task_templates_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 1)

    def test_get_assessment_task_template_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_assessment_task_template_detail_with_questions_count(self):
        response = self.client.get(self.detail_url)
        self.assertIsNotNone(response.data['questions'][0]['prompt'])

    def test_get_assessment_task_template_detail_with_questions_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(len(response.data['questions']), 5)

    def test_get_assessment_task_template_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_assessment_task_template(self):
        template = self.create_care_plan_template()

        payload = {
            'plan_template': template.id,
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
            'appear_time': datetime.time(8, 0, 0),
            'due_time': datetime.time(17, 0, 0)
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_full_update_assessment_task_template(self):
        template = self.create_care_plan_template()

        payload = {
            'plan_template': template.id,
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
            'appear_time': datetime.time(8, 0, 0),
            'due_time': datetime.time(17, 0, 0)
        }
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_assessment_task_template(self):
        payload = {
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_assessment_task_template(self):
        now = timezone.now()
        plan = self.create_care_plan()
        tasks_before = 3
        tasks_after = 5

        for i in range(tasks_before):
            days_ago = 3 - i
            self.create_assessment_task(
                plan=plan,
                assessment_task_template=self.template,
                due_datetime=now - relativedelta(days=days_ago)
            )

        for i in range(tasks_after):
            self.create_assessment_task(
                plan=plan,
                assessment_task_template=self.template,
                due_datetime=now + relativedelta(days=i, hours=1)
            )

        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.template.assessment_tasks.count(), tasks_before)

        get_response = self.client.get(self.detail_url)
        self.assertFalse(get_response.data['is_active'])


class TestAssessmentTaskTemplateUsingPatient(TasksMixin, APITestCase):
    """
    Test cases for :model:`tasks.AssessmentTaskTemplate` using a patient
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.patient = self.create_patient()
        self.user = self.patient.user

        self.template = self.create_assessment_task_template()

        self.url = reverse('assessment_task_templates-list')
        self.detail_url = reverse(
            'assessment_task_templates-detail',
            kwargs={'pk': self.template.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_assessment_task_templates_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 1)

    def test_get_assessment_task_template_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_assessment_task_template_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_assessment_task_template(self):
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

    def test_full_update_assessment_task_template(self):
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

    def test_partial_update_assessment_task_template(self):
        payload = {
            'name': self.fake.name(),
            'start_on_day': random.randint(1, 5),
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_assessment_task_template(self):
        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
