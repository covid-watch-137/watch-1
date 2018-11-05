from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from .mixins import PlansMixin


class TestCarePlanTemplatTypeUsingEmployee(PlansMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlanTemplateType` using an employee
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.template_type = self.create_care_plan_template_type()

        self.url = reverse('care_plan_template_types-list')
        self.detail_url = reverse(
            'care_plan_template_types-detail',
            kwargs={'pk': self.template_type.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_care_plan_template_types_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 1)

    def test_get_care_plan_template_type_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_care_plan_template_type_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_care_plan_template_type(self):
        payload = {
            'name': self.fake.name(),
            'acronym': self.fake.word()
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_full_update_care_plan_template_type(self):
        payload = {
            'name': self.fake.name(),
            'acronym': self.fake.word()
        }
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_care_plan_template_type(self):
        payload = {
            'name': self.fake.name(),
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_care_plan_template_type(self):
        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestCarePlanTemplateTypeUsingPatient(PlansMixin, APITestCase):
    """
    Test cases for :model:`plans.CarePlanTemplateType` using a patient
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.patient = self.create_patient()
        self.user = self.patient.user

        self.template_type = self.create_care_plan_template_type()

        self.url = reverse('care_plan_template_types-list')
        self.detail_url = reverse(
            'care_plan_template_types-detail',
            kwargs={'pk': self.template_type.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_care_plan_template_types_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 1)

    def test_get_care_plan_template_type_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_care_plan_template_type_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_care_plan_template_type(self):
        payload = {
            'name': self.fake.name(),
            'acronym': self.fake.word()
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_update_care_plan_template_type(self):
        payload = {
            'name': self.fake.name(),
            'acronym': self.fake.word()
        }
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_care_plan_template_type(self):
        payload = {
            'name': self.fake.name(),
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_care_plan_template_type(self):
        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestCarePlanTemplateByType(PlansMixin, APITestCase):
    """
    Test cases for :view:`plans.CarePlanTemplateByType`
    """

    def setUp(self):
        self.fake = Faker()
        self.organization = self.create_organization()
        self.facility = self.create_facility(self.organization)
        self.employee = self.create_employee(**{
            'organizations': [self.organization]
        })
        self.user = self.employee.user
        self.patient = self.create_patient(**{
            'facility': self.facility
        })

        self.template_type = self.create_care_plan_template_type()

        kwargs = {
            'parent_lookup_care_plans__patient__facility__organization': self.organization.id,
            'pk': self.template_type.id
        }
        self.url = reverse(
            'type-plan-templates',
            kwargs=kwargs
        )
        self.client.force_authenticate(user=self.user)

    def test_care_plan_template_by_type_detail_employee_status(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_care_plan_template_by_type_detail_patient_status(self):
        self.client.logout()
        self.client.force_authenticate(self.patient.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_care_plan_template_by_type_detail_template_count(self):
        template_count = 5
        for i in range(template_count):
            template = self.create_care_plan_template(**{
                'type': self.template_type
            })

            patient = self.create_patient(**{
                'facility': self.facility
            })

            self.create_care_plan(patient, **{
                'plan_template': template
            })

        # create dummy care plans
        for i in range(template_count):
            template = self.create_care_plan_template(**{
                'type': self.template_type
            })

            patient = self.create_patient()

            self.create_care_plan(patient, **{
                'plan_template': template
            })

        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], template_count)
