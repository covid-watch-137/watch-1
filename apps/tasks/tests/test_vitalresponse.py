import random

from django.urls import reverse

from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from .mixins import TasksMixin


class TestVitalResponseUsingEmployee(TasksMixin, APITestCase):
    """
    Test cases for :model:`tasks.VitalResponse` using an employee
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.plan = self.create_care_plan()
        self.create_care_team_member(**{
            'employee_profile': self.employee,
            'plan': self.plan
        })
        self.vital_task = self.create_vital_task(**{
            'plan': self.plan
        })
        self.template = self.vital_task.vital_task_template
        self.create_multiple_vital_questions(self.template)
        self.create_responses_to_multiple_vital_questions(
            self.template,
            self.vital_task
        )
        self.responses = self.vital_task.responses.all()
        self.vital_response = random.choice(self.responses)
        self.url = reverse('vital_responses-list')
        self.detail_url = reverse(
            'vital_responses-detail',
            kwargs={'pk': self.vital_response.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_vital_response_list(self):
        response = self.client.get(self.url)
        self.assertEqual(
            response.data['count'],
            self.responses.count()
        )

    def test_get_vital_response_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_vital_response_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_vital_response_detail_not_member(self):
        vital_response = self.create_vital_response()
        url = reverse(
            'vital_responses-detail',
            kwargs={'pk': vital_response.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_vital_response(self):
        question = self.create_vital_question(**{
            'vital_task_template': self.template
        })
        answer_type = question.answer_type

        payload = {
            'vital_task': self.vital_task.id,
            'vital_question': question.id,
            'response': self.create_string_response_by_answer_type(answer_type)
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_update_vital_response(self):
        question = self.create_vital_question(**{
            'vital_task_template': self.template
        })
        answer_type = question.answer_type

        payload = {
            'vital_task': self.vital_task.id,
            'vital_question': question.id,
            'response': self.create_string_response_by_answer_type(answer_type)
        }
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_update_vital_response_not_member(self):
        question = self.create_vital_question(**{
            'vital_task_template': self.template
        })
        answer_type = question.answer_type

        payload = {
            'vital_task': self.vital_task.id,
            'vital_question': question.id,
            'response': self.create_string_response_by_answer_type(answer_type)
        }

        vital_response = self.create_vital_response()
        url = reverse(
            'vital_responses-detail',
            kwargs={'pk': vital_response.id}
        )
        response = self.client.put(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_vital_response(self):
        answer_type = self.vital_response.question.answer_type
        payload = {
            'response': self.create_string_response_by_answer_type(answer_type)
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_vital_response_not_member(self):
        answer_type = self.vital_response.question.answer_type
        payload = {
            'response': self.create_string_response_by_answer_type(answer_type)
        }
        vital_response = self.create_vital_response()
        url = reverse(
            'vital_responses-detail',
            kwargs={'pk': vital_response.id}
        )
        response = self.client.patch(url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_vital_response(self):
        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_vital_response_not_member(self):
        vital_response = self.create_vital_response()
        url = reverse(
            'vital_responses-detail',
            kwargs={'pk': vital_response.id}
        )
        response = self.client.delete(url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
