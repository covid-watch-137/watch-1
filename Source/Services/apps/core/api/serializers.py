import datetime

import pytz

from django.db.models import Q, Avg
from django.utils import timezone

from drf_haystack.serializers import HaystackSerializerMixin
from rest_framework import serializers

from apps.accounts.serializers import SettingsUserForSerializers
from apps.core.models import (Diagnosis, EmployeeProfile, Facility,
                              InvitedEmailTemplate, Medication, Organization,
                              Procedure, ProviderRole, ProviderSpecialty,
                              ProviderTitle, Symptom)
from apps.tasks.models import (
    AssessmentTask,
    PatientTask,
    SymptomTask,
    MedicationTask,
    VitalTask,
)
from care_adopt_backend import utils

from ..mailer import EmployeeMailer
from ..search_indexes import (
    DiagnosisIndex,
    ProviderRoleIndex,
    ProviderTitleIndex,
    SymptomIndex,
)
from .mixins import RepresentationMixin


class OrganizationSerializer(serializers.ModelSerializer):
    is_manager = serializers.SerializerMethodField()

    def get_is_manager(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        employee_profile = utils.employee_profile_or_none(request.user)
        if employee_profile is None:
            return False
        return obj in employee_profile.organizations_managed.all()

    class Meta:
        model = Organization
        fields = (
            'id',
            'name',
            'is_manager',
            'addr_street',
            'addr_suite',
            'addr_city',
            'addr_state',
            'addr_zip',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'created',
            'modified',
        )


# TODO: DELETE on a facility should mark it inactive rather than removing it
# from the database.
class FacilitySerializer(RepresentationMixin, serializers.ModelSerializer):
    is_manager = serializers.SerializerMethodField()

    def get_is_manager(self, obj):
        request = self.context.get('request')
        if not request:
            return False
        employee_profile = utils.employee_profile_or_none(request.user)
        if not employee_profile:
            return False
        return obj in request.user.employee_profile.facilities_managed.all()

    def create(self, validated_data):
        instance = super(FacilitySerializer, self).create(validated_data)
        user = self.context['request'].user
        user.employee_profile.facilities_managed.add(instance)
        return instance

    class Meta:
        model = Facility
        fields = (
            'id',
            'name',
            'organization',
            'is_affiliate',
            'is_manager',
            'parent_company',
            'addr_street',
            'addr_suite',
            'addr_city',
            'addr_state',
            'addr_zip',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'is_manager',
            'created',
            'modified',
        )
        nested_serializers = [
            {
                'field': 'organization',
                'serializer_class': OrganizationSerializer,
            }
        ]


class ProviderTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderTitle
        fields = (
            'id',
            'name',
            'abbreviation',
        )
        read_only_fields = (
            'id',
        )


class ProviderTitleSearchSerializer(HaystackSerializerMixin,
                                    ProviderTitleSerializer):
    """
    Serializer to be used by the results returned by search
    for provider titles.
    """
    class Meta(ProviderTitleSerializer.Meta):
        index_classes = [ProviderTitleIndex]
        search_fields = ('text', 'name')


class ProviderRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderRole
        fields = (
            'id',
            'name',
        )
        read_only_fields = (
            'id',
        )


class ProviderRoleSearchSerializer(HaystackSerializerMixin,
                                   ProviderRoleSerializer):
    """
    Serializer to be used by the results returned by search
    for provider roles.
    """
    class Meta(ProviderRoleSerializer.Meta):
        index_classes = [ProviderRoleIndex]
        search_fields = ('text', 'name')


class ProviderSpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderSpecialty
        fields = '__all__'


class EmployeeUserInfo(SettingsUserForSerializers, serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    def get_image_url(self, obj):
        return obj.get_image_url()

    class Meta:
        read_only_fields = ('email', 'date_joined', 'last_login', 'image_url', )
        exclude = ('password', 'is_superuser', 'groups', 'user_permissions',
                   'validation_key', 'validated_at', 'reset_key', 'is_developer',
                   'image', )


class EmployeeProfileSerializer(RepresentationMixin, serializers.ModelSerializer):

    class Meta:
        model = EmployeeProfile
        fields = (
            'id',
            'user',
            'status',
            'npi_code',
            'organizations',
            'organizations_managed',
            'facilities',
            'facilities_managed',
            'title',
            'roles',
            'specialty',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'created',
            'modified',
        )
        nested_serializers = [
            {
                'field': 'user',
                'serializer_class': EmployeeUserInfo,
            },
            {
                'field': 'specialty',
                'serializer_class': ProviderSpecialtySerializer,
            },
            {
                'field': 'title',
                'serializer_class': ProviderTitleSerializer,
            },
            {
                'field': 'organizations',
                'serializer_class': OrganizationSerializer,
                'many': True,
            },
            {
                'field': 'organizations_managed',
                'serializer_class': OrganizationSerializer,
                'many': True,
            },
            {
                'field': 'facilities',
                'serializer_class': FacilitySerializer,
                'many': True,
            },
            {
                'field': 'facilities_managed',
                'serializer_class': FacilitySerializer,
                'many': True,
            },
        ]


class EmployeeAssignmentSerializer(serializers.ModelSerializer):
    """
    Serializer to be used for employee's assignment details
    for the current month-to-date
    """
    risk_level = serializers.SerializerMethodField()

    class Meta:
        model = EmployeeProfile
        fields = (
            'id',
            'facilities_count',
            'care_manager_count',
            'care_team_count',
            'billable_patients_count',
            'risk_level',
        )

    def get_average_assessment(self, kwargs):
        tasks = AssessmentTask.objects.filter(**kwargs).aggregate(
            average=Avg('responses__rating'))
        average = tasks['average'] or 0
        avg = round((average / 5) * 100)
        return avg

    def get_average_engagement(self, task_kwargs):
        kwargs = task_kwargs.pop('kwargs')
        medication_kwargs = task_kwargs.pop('medication_kwargs')
        patient_tasks = PatientTask.objects.filter(**kwargs)
        medication_tasks = MedicationTask.objects.filter(
            **medication_kwargs)
        symptom_tasks = SymptomTask.objects.filter(**kwargs)
        assessment_tasks = AssessmentTask.objects.filter(**kwargs)
        vital_tasks = VitalTask.objects.filter(**kwargs)

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

    def get_risk_level(self, obj):
        now = timezone.now()
        first_day = now.date().replace(day=1)
        due_datetime = datetime.datetime.combine(first_day,
                                                 datetime.time.min,
                                                 tzinfo=pytz.utc)
        plans = obj.assigned_roles.values_list('plan', flat=True).distinct()
        outcome_kwargs = {
            'plan__in': plans,
            'assessment_task_template__tracks_outcome': True
        }
        outcome = self.get_average_assessment(outcome_kwargs)

        kwargs = {
            'plan__in': plans,
            'due_datetime__gte': due_datetime
        }
        medication_kwargs = {
            'medication_task_template__plan__in': plans,
            'due_datetime__gte': due_datetime
        }
        task_kwargs = {
            'kwargs': kwargs,
            'medication_kwargs': medication_kwargs
        }
        engagement = self.get_average_engagement(task_kwargs)
        return round((outcome + engagement) / 2)


class OrganizationEmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer to be used for employees inside an organization
    """
    full_name = serializers.SerializerMethodField()
    facilities_count = serializers.SerializerMethodField()
    image_url = serializers.ReadOnlyField(source='user.image_url')
    title = serializers.ReadOnlyField(source='title.name')

    class Meta:
        model = EmployeeProfile
        fields = (
            'id',
            'full_name',
            'image_url',
            'title',
            'status',
            'facilities_count',
        )

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_facilities_count(self, obj):
        queryset = Facility.objects.filter(
            Q(id__in=obj.facilities.all()) |
            Q(id__in=obj.facilities_managed.all()),
        ).distinct()
        return queryset.count()


class FacilityEmployeeSerializer(serializers.ModelSerializer):
    """
    Serializer to be used for employees inside a facility
    """
    full_name = serializers.SerializerMethodField()
    care_manager = serializers.SerializerMethodField()
    care_team = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    other_facilities = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    title = serializers.ReadOnlyField(source='title.name')

    class Meta:
        model = EmployeeProfile
        fields = (
            'id',
            'full_name',
            'image_url',
            'title',
            'status',
            'care_manager',
            'care_team',
            'is_admin',
            'other_facilities',
        )

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_image_url(self, obj):
        return obj.user.get_image_url()

    def get_care_manager(self, obj):
        return obj.assigned_roles.filter(is_manager=True).count()

    def get_care_team(self, obj):
        return obj.assigned_roles.filter(is_manager=False).count()

    def get_is_admin(self, obj):
        facility = self.context['facility']
        return facility.organization in obj.organizations_managed.all() or \
            facility in obj.facilities_managed.all()

    def get_other_facilities(self, obj):
        facility = self.context['facility']
        queryset = Facility.objects.filter(
            Q(id__in=obj.facilities.all()) |
            Q(id__in=obj.facilities_managed.all()),
        ).exclude(id=facility.id).distinct()
        return queryset.count()


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = '__all__'


class DiagnosisSearchSerializer(HaystackSerializerMixin,
                                DiagnosisSerializer):
    """
    Serializer to be used by the results returned by search
    for diagnosis.
    """
    class Meta(DiagnosisSerializer.Meta):
        index_classes = [DiagnosisIndex]
        search_fields = ('text', 'name', 'dx_code')


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = (
            'id',
            'name',
            'rx_code',
        )
        read_only_fields = (
            'id',
        )


class ProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procedure
        fields = '__all__'


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = '__all__'


class InvitedEmailTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvitedEmailTemplate
        fields = [
            'subject',
            'message',
            'is_default',
        ]


class SymptomSearchSerializer(HaystackSerializerMixin,
                              SymptomSerializer):
    """
    Serializer to be used by the results returned by search
    for symptoms.
    """
    class Meta(SymptomSerializer.Meta):
        index_classes = [SymptomIndex]
        search_fields = ('text', 'name')


class EmployeeIDSerializer(serializers.ModelSerializer):
    """
    Serializer to be used for :model:`core.EmployeeProfile` with ID field.
    """

    class Meta:
        model = EmployeeProfile
        fields = (
            'id',
        )


class InviteEmployeeSerializer(serializers.Serializer):
    """
    Serializer to be used for sending an invitation email to multiple employees
    """

    employees = serializers.ListField(
        child=serializers.UUIDField(),
        min_length=1
    )
    email_content = serializers.CharField(max_length=1000)

    def validate_employees(self, value):
        employees = []
        for employee_id in value:
            try:
                employee = EmployeeProfile.objects.get(id=employee_id)
                employees.append(employee)
            except EmployeeProfile.DoesNotExist:
                raise serializers.ValidationError(
                    f'Employee ID: {employee_id} does not exist.'
                )
        return employees

    def save(self):
        employees = self.validated_data['employees']
        email_content = self.validated_data['email_content']

        mailer = EmployeeMailer()
        for employee in employees:
            mailer.send_invitation(employee, email_content)
