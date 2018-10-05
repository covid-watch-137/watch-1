from unittest import mock

from django.db.models import Avg
from django.urls import reverse
from django.utils import timezone

from faker import Faker
from rest_framework.test import APITestCase

from ..models import PatientProfile
from ..tests.mixins import PatientsMixin
from apps.tasks.models import AssessmentResponse
from apps.tasks.tests.mixins import TasksMixin
from apps.tasks.utils import (
    calculate_task_percentage,
    get_all_tasks_of_patient_today,
)


class TestPatientProfile(PatientsMixin, APITestCase):
    """
    Test cases for :model:`tasks.PatientProfile` using a patient
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.patient = self.create_patient()
        self.other_patient = self.create_patient()
        self.user = self.patient.user

        self.detail_url = reverse(
            'patient_profiles-detail',
            kwargs={'pk': self.patient.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_patient_detail_with_facility(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(
            response.data['facility']['name'],
            self.patient.facility.name
        )


class TestPatientProfileUsingEmployee(PatientsMixin, APITestCase):
    """
    Test cases for :model:`tasks.PatientProfile` using an employee
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user
        self.client.force_authenticate(user=self.user)

    def test_create_verification_code_on_invite(self):
        patient = self.create_patient(**{
            'status': 'invited'
        })
        self.assertTrue(patient.verification_codes.exists())


class TestPatientProfileSearchViewSet(PatientsMixin, APITestCase):
    """
    Test cases for :view:`patients.PatientProfileSearchViewSet` using an employee as the logged in user.
    """
    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.client.force_authenticate(user=self.employee.user)

    @mock.patch('apps.patients.api.views.get_searchable_patients')
    def test_search_patients_via_haystack_with_search_query(self, get_searchable_patients):
        """
        search view should call `get_searchable_patients` function if the GET request has `q` data
        """
        search_url = reverse('patient_profiles_search-list') + '?q=' + 'Patient Name'

        response = self.client.get(search_url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(get_searchable_patients.called)

    @mock.patch('apps.patients.api.views.get_searchable_patients')
    def test_search_patients_via_haystack_without_search_query(self, get_searchable_patients):
        """
        search view should return no data if the GET request does not contain `q` data
        """
        search_url = reverse('patient_profiles_search-list')

        response = self.client.get(search_url)

        self.assertFalse(get_searchable_patients.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)


class TestPatientProfileDashboard(TasksMixin, APITestCase):
    """
    Test cases for :model:`tasks.PatientTask` using a patient
    as the logged in user. This test case is specific to the
    patient dashboard.
    """

    def setUp(self):
        self.fake = Faker()
        self.patient = self.create_patient()
        self.other_patient = self.create_patient()
        self.user = self.patient.user

        self.plan = self.create_care_plan(patient=self.patient)
        self.generate_patient_tasks()
        self.generate_medication_tasks()
        self.generate_symptom_tasks()
        self.generate_assessment_tasks_with_questions_and_responses()

        self.dashboard_url = reverse('patient-dashboard')
        self.client.force_authenticate(user=self.user)

    def generate_patient_tasks(self):
        for i in range(3):
            # Create PatientTask with status `undefined`
            self.create_patient_task(**{'plan': self.plan})

            # Create PatientTask with status `done`
            self.create_patient_task(**{
                'plan': self.plan,
                'status': 'done'
            })

    def generate_medication_tasks(self):
        template = self.create_medication_task_template(plan=self.plan)
        for i in range(3):
            # Create MedicationTask with status `undefined`
            self.create_medication_task(**{
                'medication_task_template': template
            })

            # Create MedicationTask with status `done`
            self.create_medication_task(**{
                'medication_task_template': template,
                'status': 'done'
            })

    def generate_symptom_tasks(self):
        for i in range(5):
            self.create_symptom_task(**{
                'plan': self.plan
            })

            if i < 3:
                task = self.create_symptom_task(**{
                    'plan': self.plan
                })
                self.create_symptom_rating(symptom_task=task)

    def generate_assessment_tasks_with_questions_and_responses(self):
        for i in range(5):

            template = self.create_assessment_task_template(**{
                'tracks_outcome': True
            })
            task = self.create_assessment_task(**{
                'plan': self.plan,
                'assessment_task_template': template
            })

            # Create questions and responses
            for q in range(6):
                question = self.create_assessment_question(
                    task.assessment_task_template
                )

                if i < 4:
                    self.create_assessment_response(task, question)

    def test_get_patient_dashboard_task_percentage(self):
        percentage = calculate_task_percentage(self.patient)
        response = self.client.get(self.dashboard_url)
        patient = response.data['results'][0]
        self.assertEqual(patient['task_percentage'], percentage)

    def test_get_assessment_score(self):
        now = timezone.now()
        responses = AssessmentResponse.objects.filter(
            assessment_task__appear_datetime__lte=now,
            assessment_task__plan__patient=self.patient,
            assessment_task__assessment_task_template__tracks_outcome=True
        )
        average = responses.aggregate(score=Avg('rating'))
        score = round(average['score']) if average['score'] else 0
        response = self.client.get(self.dashboard_url)
        patient = response.data['results'][0]
        self.assertEqual(patient['assessment_score'], score)

    def test_get_tasks_today(self):
        tasks = get_all_tasks_of_patient_today(self.patient)
        response = self.client.get(self.dashboard_url)
        patient = response.data['results'][0]
        self.assertEqual(len(patient['tasks_today']), len(tasks))

    def test_filter_patient_dashboard_by_id(self):
        # Use an employee account to get list of patients in the queryset
        self.client.logout()
        employee = self.create_employee()
        self.client.force_authenticate(user=employee.user)

        for patient in PatientProfile.objects.all():
            employee.facilities.add(patient.facility)

        filter_url = f'{self.dashboard_url}?id={self.patient.id}'
        response = self.client.get(filter_url)
        self.assertEqual(response.data['count'], 1)
