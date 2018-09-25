from rest_framework import serializers

from care_adopt_backend import utils
from apps.accounts.serializers import SettingsUserForSerializers
from apps.core.models import (
    Organization, Facility, EmployeeProfile, ProviderTitle, ProviderRole,
    ProviderSpecialty, Diagnosis, Medication, Procedure, Symptom, )


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
        fields = '__all__'


# TODO: DELETE on a facility should mark it inactive rather than removing it
# from the database.
class FacilitySerializer(serializers.ModelSerializer):
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

    def to_representation(self, instance):
        data = super(FacilitySerializer, self).to_representation(instance)
        if instance.organization:
            organization = OrganizationSerializer(
                instance.organization
            )
            data.update({
                'organization': organization.data
            })
        return data


class ProviderTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderTitle
        fields = '__all__'


class ProviderRoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProviderRole
        fields = '__all__'


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


class EmployeeProfileSerializer(serializers.ModelSerializer):

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

    def to_representation(self, instance):
        data = super(EmployeeProfileSerializer, self).to_representation(
            instance)

        if instance.user:
            user = EmployeeUserInfo(instance.user)
            data.update({
                'user': user.data
            })

        if instance.specialty:
            specialty = ProviderSpecialtySerializer(
                instance.specialty
            )
            data.update({
                'specialty': specialty.data
            })

        if instance.title:
            title = ProviderTitleSerializer(
                instance.title
            )
            data.update({
                'title': title.data
            })

        if instance.organizations.exists():
            organizations = OrganizationSerializer(
                instance.organizations.all(),
                many=True
            )
            data.update({
                'organizations': organizations.data
            })

        if instance.organizations_managed.exists():
            organizations_managed = OrganizationSerializer(
                instance.organizations_managed.all(),
                many=True
            )
            data.update({
                'organizations_managed': organizations_managed.data
            })

        if instance.facilities.exists():
            facilities = FacilitySerializer(
                instance.facilities.all(),
                many=True
            )
            data.update({
                'facilities': facilities.data
            })

        if instance.facilities_managed.exists():
            facilities_managed = FacilitySerializer(
                instance.facilities_managed.all(),
                many=True
            )
            data.update({
                'facilities_managed': facilities_managed.data
            })

        return data


class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = '__all__'


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = '__all__'


class ProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Procedure
        fields = '__all__'


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = '__all__'
