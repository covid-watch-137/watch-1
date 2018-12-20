from django.db.models import Q

from drf_haystack.serializers import HaystackSerializerMixin
from rest_framework import serializers

from apps.accounts.serializers import SettingsUserForSerializers
from apps.core.models import (Diagnosis, EmployeeProfile, Facility,
                              InvitedEmailTemplate, Medication, Organization,
                              Procedure, ProviderRole, ProviderSpecialty,
                              ProviderTitle, Symptom)
from care_adopt_backend import utils

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
        request = self.context['request']
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
        request = self.context['request']
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
