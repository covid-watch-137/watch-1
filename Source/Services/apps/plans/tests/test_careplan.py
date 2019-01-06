import math
import pytz
import random

from datetime import datetime, time, timedelta

from django.apps import apps
from django.db.models import Avg
from django.urls import reverse
from django.utils import timezone

from dateutil import rrule
from dateutil.relativedelta import relativedelta
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from .mixins import PlansMixin
from apps.tasks.models import (
    PatientTask,
    MedicationTask,
    TeamTask,
    SymptomTask,
    AssessmentTask,
    VitalTask,
)
from apps.tasks.tests.mixins import TasksMixin
from apps.accounts.tests.factories import RegularUserFactory


class TestCarePlanUsingEmployee(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan1 using an employee as the logged in
    user.
    """
    def setUp(self):
        self.fake = Faker()
        self.patient = self.create_patient()
        self.facility = self.create_facility()
        self.employee = self.create_employee(**{
            'facilities': [self.facility]
        })
        self.user = self.employee.user

        self.plan_template = self.create_care_plan_template()
        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan(self):
        # Given a `CarePlan` that is using a `CarePlanTemplate`
        # with 1 `GoalTemplate`
        self.goal_template = self.create_goal_template(
            plan_template=self.plan_template,
        )

        # When a new `CarePlan` is created
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id,
        }
        self.client.post(self.url, payload)

        Goal = apps.get_model('plans.Goal')

        # Then `Goal`s should created for every `GoalTemplate` under the
        # `CarePlan`'s `CarePlanTemplate`
        self.assertEqual(Goal.objects.count(), 1)

        # Then Created `Goal`s should have a `start_on_datetime` equal to
        # current date plus the `GoalTemplate`'s `start_on_day`
        goal = Goal.objects.first()
        expected_start_on_datetime = timezone.now() + timedelta(
            days=self.goal_template.start_on_day)

        self.assertAlmostEqual(
            goal.start_on_datetime,
            expected_start_on_datetime,
            delta=timedelta(seconds=1),
        )

    def test_care_plan_average_total_patient(self):
        facility = self.create_facility()
        organization = facility.organization
        total_patients = 5

        for i in range(total_patients):
            patient = self.create_patient(**{
                'facility': facility
            })
            self.create_care_plan(patient)

        # Create patients for other facility
        for i in range(3):
            self.create_patient()

        url = reverse('care_plans-average')
        avg_url = f'{url}?patient__facility__organization={organization.id}'
        response = self.client.get(avg_url)
        self.assertEqual(response.data['total_patients'], total_patients)

    def test_care_plan_average_total_facility(self):
        organization = self.create_organization()
        total_facilities = 5

        for i in range(total_facilities):
            facility = self.create_facility(organization)
            patient = self.create_patient(**{
                'facility': facility
            })
            self.create_care_plan(patient)

        # Create patients for other organization
        for i in range(3):
            self.create_patient()

        url = reverse('care_plans-average')
        avg_url = f'{url}?patient__facility__organization={organization.id}'
        response = self.client.get(avg_url)
        self.assertEqual(response.data['total_patients'], total_facilities)

    def test_care_plan_average_total_care_plans(self):
        organization = self.create_organization()
        total_care_plans = 5

        for i in range(total_care_plans):
            facility = self.create_facility(organization)
            patient = self.create_patient(**{
                'facility': facility
            })
            self.create_care_plan(patient)

        # Create patients for other organization
        for i in range(3):
            self.create_care_plan()

        url = reverse('care_plans-average')
        avg_url = f'{url}?patient__facility__organization={organization.id}'
        response = self.client.get(avg_url)
        self.assertEqual(response.data['total_patients'], total_care_plans)

    def generate_average_outcome_records(self, organization):
        total_facilities = 3
        total_care_plans = 5
        total_patients = 6
        num_assessment_tasks = 3
        plans = []

        for i in range(total_facilities):
            facility = self.create_facility(organization)
            for p in range(total_patients):
                patient = self.create_patient(**{
                    'facility': facility
                })
                for c in range(total_care_plans):
                    plan = self.create_care_plan(patient)
                    plans.append(plan)

                    for t in range(num_assessment_tasks):
                        template = self.create_assessment_task_template(**{
                            'tracks_outcome': True
                        })
                        task = self.create_assessment_task(**{
                            'plan': plan,
                            'assessment_task_template': template
                        })
                        questions = template.questions.all()
                        self.create_responses_to_multiple_questions(template,
                                                                    task,
                                                                    questions)

        outcome_tasks = AssessmentTask.objects.filter(
            plan__in=plans,
            assessment_task_template__tracks_outcome=True
        ).aggregate(outcome_average=Avg('responses__rating'))
        average = outcome_tasks['outcome_average'] or 0
        average_outcome = round((average / 5) * 100)

        # Create dummy record
        for i in range(5):
            template = self.create_assessment_task_template(**{
                'tracks_outcome': True
            })
            task = self.create_assessment_task(**{
                'assessment_task_template': template
            })
            self.create_multiple_assessment_questions(template)
            questions = template.questions.all()
            self.create_responses_to_multiple_questions(
                template, task, questions)

        return average_outcome

    def generate_average_engagement_records(self, organization):
        total_facilities = 3
        total_care_plans = 5
        total_patients = 6
        plans = []
        now = timezone.now()
        due_datetime = now - relativedelta(days=3)

        for i in range(total_facilities):
            facility = self.create_facility(organization)
            for p in range(total_patients):
                patient = self.create_patient(**{
                    'facility': facility
                })
                for c in range(total_care_plans):
                    plan = self.create_care_plan(patient)
                    plans.append(plan)

                    self.generate_assessment_tasks(plan, due_datetime)
                    self.generate_patient_tasks(plan, due_datetime)
                    self.generate_medication_tasks(plan, due_datetime)
                    self.generate_symptom_tasks(plan, due_datetime)
                    self.generate_vital_tasks(plan, due_datetime)

        assessment_tasks = AssessmentTask.objects.filter(
            plan__in=plans,
            due_datetime__lte=now
        )
        patient_tasks = PatientTask.objects.filter(
            plan__in=plans,
            due_datetime__lte=now
        )
        medication_tasks = MedicationTask.objects.filter(
            medication_task_template__plan__in=plans,
            due_datetime__lte=now
        )
        symptom_tasks = SymptomTask.objects.filter(
            plan__in=plans,
            due_datetime__lte=now
        )
        vital_tasks = VitalTask.objects.filter(
            plan__in=plans,
            due_datetime__lte=now
        )
        total_patient_tasks = patient_tasks.count()
        total_medication_tasks = medication_tasks.count()
        total_symptom_tasks = symptom_tasks.count()
        total_assessment_tasks = assessment_tasks.count()
        total_vital_tasks = vital_tasks.count()

        completed_patient_tasks = patient_tasks.filter(
            status__in=['missed', 'done']).count()
        completed_medication_tasks = medication_tasks.filter(
            status__in=['missed', 'done']).count()
        completed_symptom_tasks = symptom_tasks.filter(
            is_complete=True).count()
        completed_assessment_tasks = assessment_tasks.filter(
            is_complete=True).count()
        completed_vital_tasks = vital_tasks.filter(
            is_complete=True).count()
        total_completed = (completed_patient_tasks +
                           completed_medication_tasks +
                           completed_symptom_tasks +
                           completed_assessment_tasks +
                           completed_vital_tasks)
        total_tasks = (total_patient_tasks +
                       total_medication_tasks +
                       total_symptom_tasks +
                       total_assessment_tasks +
                       total_vital_tasks)
        return round((total_completed / total_tasks) * 100) \
            if total_tasks > 0 else 0

    def test_care_plan_average_outcome(self):
        organization = self.create_organization()
        average_outcome = self.generate_average_outcome_records(organization)

        url = reverse('care_plans-average')
        avg_url = f'{url}?patient__facility__organization={organization.id}'
        response = self.client.get(avg_url)
        self.assertEqual(response.data['average_outcome'], average_outcome)

    def test_care_plan_average_engagement(self):
        organization = self.create_organization()
        average_engagement = self.generate_average_engagement_records(
            organization)

        url = reverse('care_plans-average')
        avg_url = f'{url}?patient__facility__organization={organization.id}'
        response = self.client.get(avg_url)
        self.assertEqual(
            response.data['average_engagement'],
            average_engagement
        )

    def test_care_plan_average_risk_level(self):
        organization = self.create_organization()
        average_outcome = self.generate_average_outcome_records(organization)
        average_engagement = self.generate_average_engagement_records(
            organization)
        risk_level = round((average_outcome + average_engagement) / 2)

        url = reverse('care_plans-average')
        avg_url = f'{url}?patient__facility__organization={organization.id}'
        response = self.client.get(avg_url)
        self.assertAlmostEqual(response.data['risk_level'], risk_level)

    def test_care_plan_average_unauthorized(self):
        self.client.logout()
        url = reverse('care_plans-average')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_care_plan_average_patient_unauthorized(self):
        self.client.logout()
        patient = self.create_patient()
        self.client.force_authenticate(patient.user)
        url = reverse('care_plans-average')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_care_plan_by_facility(self):
        patient_count = 5
        plan_count = 3
        total_count = patient_count * plan_count

        for i in range(patient_count):
            patient = self.create_patient(**{
                'facility': self.facility
            })

            for p in range(plan_count):
                self.create_care_plan(patient)

        # Create dummy records
        for i in range(patient_count):
            patient = self.create_patient()

            for p in range(plan_count):
                self.create_care_plan(patient)

        url = reverse(
            'facility-care-plans-list',
            kwargs={'parent_lookup_patient__facility': self.facility.id}
        )
        response = self.client.get(url)
        self.assertEqual(response.data['count'], total_count)


class TestCarePlanPostSaveSignalFrequencyOnce(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with once frequency
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.plan_template = self.create_care_plan_template()
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task(self):
        self.create_patient_task_template(
            self.plan_template)
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, 1)

    def test_create_care_plan_team_task(self):
        self.create_team_task_template(**{
            'plan_template': self.plan_template
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, 1)

    def test_create_care_plan_symptom_task(self):
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'once'
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, 1)

    def test_create_care_plan_assessment_task(self):
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'once'
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, 1)

    def test_create_care_plan_vital_task(self):
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'once'
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, 1)


class TestCarePlanPostSaveSignalDailyWithRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with daily frequency
    and with repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.plan_template = self.create_care_plan_template()
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'daily',
                'repeat_amount': repeat_amount
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_team_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'daily',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_symptom_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'daily',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_assessment_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'daily',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_vital_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'daily',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)


class TestCarePlanPostSaveSignalDailyWithoutRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with daily frequency
    and without repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.duration_weeks = random.randint(1, 3)
        self.duration_days = self.duration_weeks * 7
        self.plan_template = self.create_care_plan_template(**{
            'duration_weeks': self.duration_weeks
        })
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
        )
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'daily',
                'start_on_day': start_on_day
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_team_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
        )
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'daily',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_symptom_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
        )
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'daily',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_assessment_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
        )
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'daily',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_vital_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
        )
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'daily',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())


class TestCarePlanPostSaveSignalWeeklyWithRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with weekly frequency
    and with repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.plan_template = self.create_care_plan_template()
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'weekly',
                'repeat_amount': repeat_amount
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_team_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekly',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_symptom_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekly',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_assessment_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekly',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_vital_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekly',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)


class TestCarePlanPostSaveSignalWeeklyWithoutRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with weekly frequency
    and without repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.duration_weeks = random.randint(1, 3)
        self.duration_days = self.duration_weeks * 7
        self.plan_template = self.create_care_plan_template(**{
            'duration_weeks': self.duration_weeks
        })
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_without_repeat(self):
        start_on_day = random.randint(2, 5)
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'weekly',
                'start_on_day': start_on_day
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, self.duration_weeks)

    def test_create_care_plan_team_task_without_repeat(self):
        start_on_day = random.randint(2, 5)
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekly',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, self.duration_weeks)

    def test_create_care_plan_symptom_task_without_repeat(self):
        start_on_day = random.randint(2, 5)
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekly',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, self.duration_weeks)

    def test_create_care_plan_assessment_task_without_repeat(self):
        start_on_day = random.randint(2, 5)
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekly',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, self.duration_weeks)

    def test_create_care_plan_vital_task_without_repeat(self):
        start_on_day = random.randint(2, 5)
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekly',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, self.duration_weeks)


class TestCarePlanPostSaveSignalOtherDayWithRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with every_other_day frequency
    and with repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.plan_template = self.create_care_plan_template()
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'every_other_day',
                'repeat_amount': repeat_amount
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_team_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'every_other_day',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_symptom_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'every_other_day',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_assessment_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'every_other_day',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_vital_task_with_repeat(self):
        repeat_amount = random.randint(2, 5)
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'every_other_day',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)


class TestCarePlanPostSaveSignalOtherDayWithoutRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with every_other_day frequency
    and without repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.duration_weeks = random.randint(1, 3)
        self.duration_days = self.duration_weeks * 7
        self.plan_template = self.create_care_plan_template(**{
            'duration_weeks': self.duration_weeks
        })
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        days = rrule.rrule(
            rrule.DAILY,
            interval=2,
            dtstart=start,
            until=end,
        )
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'every_other_day',
                'start_on_day': start_on_day
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_team_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        days = rrule.rrule(
            rrule.DAILY,
            interval=2,
            dtstart=start,
            until=end,
        )
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'every_other_day',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_symptom_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        days = rrule.rrule(
            rrule.DAILY,
            interval=2,
            dtstart=start,
            until=end,
        )
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'every_other_day',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_assessment_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        days = rrule.rrule(
            rrule.DAILY,
            interval=2,
            dtstart=start,
            until=end,
        )
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'every_other_day',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_vital_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(days=self.duration_days)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        days = rrule.rrule(
            rrule.DAILY,
            interval=2,
            dtstart=start,
            until=end,
        )
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'every_other_day',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())


class TestCarePlanPostSaveSignalWeekdaysWithRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with weekdays frequency
    and with repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.plan_template = self.create_care_plan_template()
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'weekdays',
                'repeat_amount': repeat_amount
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_team_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekdays',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_symptom_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekdays',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_assessment_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekdays',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_vital_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekdays',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)


class TestCarePlanPostSaveSignalWeekdaysWithoutRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with weekdays frequency
    and without repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.duration_weeks = random.randint(1, 3)
        self.duration_days = self.duration_weeks * 7
        self.plan_template = self.create_care_plan_template(**{
            'duration_weeks': self.duration_weeks
        })
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(weeks=self.duration_weeks)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        weekdays = [0, 1, 2, 3, 4]
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
            byweekday=weekdays
        )
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'weekdays',
                'start_on_day': start_on_day
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        tasks = PatientTask.objects.filter(
            plan__id=response.data['id'])
        count = tasks.count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_team_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(weeks=self.duration_weeks)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        weekdays = [0, 1, 2, 3, 4]
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
            byweekday=weekdays
        )
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekdays',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_symptom_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(weeks=self.duration_weeks)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        weekdays = [0, 1, 2, 3, 4]
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
            byweekday=weekdays
        )
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekdays',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_assessment_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(weeks=self.duration_weeks)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        weekdays = [0, 1, 2, 3, 4]
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
            byweekday=weekdays
        )
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekdays',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())

    def test_create_care_plan_vital_task_without_repeat(self):
        now = timezone.now()
        start_on_day = random.randint(2, 5)
        start = now + relativedelta(days=start_on_day)
        end = now + relativedelta(weeks=self.duration_weeks)
        end = datetime.combine(end.date(), time.max, tzinfo=pytz.utc)
        weekdays = [0, 1, 2, 3, 4]
        days = rrule.rrule(
            rrule.DAILY,
            dtstart=start,
            until=end,
            byweekday=weekdays
        )
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekdays',
            'start_on_day': start_on_day
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, days.count())


class TestCarePlanPostSaveSignalWeekendsWithRepeat(TasksMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlan` using an employee
    as the logged in user. This is particularly testing the
    post_save signal of the CarePlan model with weekends frequency
    and with repeat_amount
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.plan_template = self.create_care_plan_template()
        self.patient_user = RegularUserFactory(time_zone='Asia/Manila')
        self.patient = self.create_patient(self.patient_user)

        self.url = reverse('care_plans-list')
        self.client.force_authenticate(user=self.user)

    def test_create_care_plan_patient_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_patient_task_template(
            self.plan_template,
            **{
                'frequency': 'weekends',
                'repeat_amount': repeat_amount
            }
        )
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = PatientTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_team_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_team_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekends',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = TeamTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_symptom_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_symptom_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekends',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = SymptomTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_assessment_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_assessment_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekends',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = AssessmentTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)

    def test_create_care_plan_vital_task_with_repeat(self):
        repeat_amount = random.randint(5, 30)
        self.create_vital_task_template(**{
            'plan_template': self.plan_template,
            'frequency': 'weekends',
            'repeat_amount': repeat_amount
        })
        payload = {
            'patient': self.patient.id,
            'plan_template': self.plan_template.id
        }

        response = self.client.post(self.url, payload)
        count = VitalTask.objects.filter(
            plan__id=response.data['id']).count()
        self.assertEqual(count, repeat_amount)
