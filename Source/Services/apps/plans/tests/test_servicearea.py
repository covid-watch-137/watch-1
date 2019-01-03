from django.urls import reverse
from faker import Faker
from rest_framework import status
from rest_framework.test import APITestCase

from .mixins import PlansMixin


class TestServiceAreaUsingEmployee(PlansMixin, APITestCase):
    """
    Test cases for :model:`plans.ServiceArea` using an employee
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.employee = self.create_employee()
        self.user = self.employee.user

        self.service_area = self.create_service_area()
        self.url = reverse('service_areas-list')
        self.detail_url = reverse(
            'service_areas-detail',
            kwargs={'pk': self.service_area.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_service_areas_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 1)

    def test_get_service_area_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_service_area_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_service_area(self):
        payload = {
            'name': self.fake.name()
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_full_update_service_area(self):
        payload = {
            'name': self.fake.name()
        }
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_service_area(self):
        payload = {
            'name': self.fake.name(),
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_service_area(self):
        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class TestServiceAreaUsingPatient(PlansMixin, APITestCase):
    """
    Test cases for :model:`plans.ServiceArea` using a patient
    as the logged in user.
    """

    def setUp(self):
        self.fake = Faker()
        self.patient = self.create_patient()
        self.user = self.patient.user

        self.service_area = self.create_service_area()

        self.url = reverse('service_areas-list')
        self.detail_url = reverse(
            'service_areas-detail',
            kwargs={'pk': self.service_area.id}
        )
        self.client.force_authenticate(user=self.user)

    def test_get_service_areas_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], 1)

    def test_get_service_area_detail(self):
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_service_area_detail_unauthenticated(self):
        self.client.logout()
        response = self.client.get(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_service_area(self):
        payload = {
            'name': self.fake.name()
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_full_update_service_area(self):
        payload = {
            'name': self.fake.name()
        }
        response = self.client.put(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_partial_update_service_area(self):
        payload = {
            'name': self.fake.name(),
        }
        response = self.client.patch(self.detail_url, payload)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_service_area(self):
        response = self.client.delete(self.detail_url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class TestCarePlanTemplateByServiceArea(PlansMixin, APITestCase):
    """
    Test cases for :view:`plans.CarePlanTemplateByServiceArea`
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

        self.service_area = self.create_service_area()

        kwargs = {
            'parent_lookup_care_plans__patient__facility__organization': self.organization.id,
            'pk': self.service_area.id
        }
        self.url = reverse(
            'service-area-plan-templates',
            kwargs=kwargs
        )
        self.client.force_authenticate(user=self.user)

    def test_care_plan_template_by_service_area_detail_employee_status(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_care_plan_template_by_service_area_detail_patient_status(self):
        self.client.logout()
        self.client.force_authenticate(self.patient.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_care_plan_template_by_service_area_detail_template_count(self):
        template_count = 5
        for i in range(template_count):
            template = self.create_care_plan_template(**{
                'service_area': self.service_area
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
                'service_area': self.service_area
            })

            patient = self.create_patient()

            self.create_care_plan(patient, **{
                'plan_template': template
            })

        response = self.client.get(self.url)
        self.assertEqual(response.data['count'], template_count)
