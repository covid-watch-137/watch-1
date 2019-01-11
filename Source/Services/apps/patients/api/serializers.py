import logging

from django.db.models import Avg
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from dateutil.relativedelta import relativedelta
from drf_haystack.serializers import HaystackSerializerMixin
from rest_framework import serializers
from rest_framework.authtoken.models import Token

from apps.accounts.forms import CustomSetPasswordForm
from apps.accounts.serializers import SettingsUserForSerializers
from apps.core.api.mixins import RepresentationMixin
from apps.core.models import EmployeeProfile
from apps.core.api.serializers import (
    FacilitySerializer,
    MedicationSerializer,
    EmployeeUserInfo,
    ProviderTitleSerializer,
    SymptomSerializer,
)
from apps.patients.models import (PatientDiagnosis, PatientMedication,
                                  PatientProcedure, PatientProfile,
                                  ProblemArea, PatientVerificationCode,
                                  ReminderEmail, PotentialPatient)
from apps.plans.api.serializers import InfoMessageSerializer
from apps.tasks.models import AssessmentResponse, SymptomRating

from ..search_indexes import PatientProfileIndex


class PatientUserInfo(SettingsUserForSerializers, serializers.ModelSerializer):
    class Meta:
        read_only_fields = ('email', 'date_joined', 'last_login', )
        exclude = ('password', 'is_superuser', 'groups', 'user_permissions',
                   'validation_key', 'validated_at', 'reset_key',
                   'is_developer', )


class PatientSearchUserInfo(SettingsUserForSerializers,
                            serializers.ModelSerializer):
    class Meta:
        fields = ('first_name', 'last_name', )


class PatientSearchSerializer(serializers.ModelSerializer):
    user = PatientSearchUserInfo()

    class Meta:
        model = PatientProfile
        fields = ('id', 'user', )


class BasicPatientSerializer(serializers.ModelSerializer):
    """
    Consists only the patient's name and ID
    """

    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = (
            'id',
            'first_name',
            'last_name',
        )

    def get_first_name(self, obj):
        return obj.user.first_name

    def get_last_name(self, obj):
        return obj.user.last_name


class PatientProfileSerializer(RepresentationMixin,
                               serializers.ModelSerializer):

    class Meta:
        model = PatientProfile
        fields = (
            'id',
            'user',
            'facility',
            'emr_code',
            'is_active',
            'is_invited',
            'last_app_use',
            'diagnosis',
            'message_for_day',
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
                'serializer_class': PatientUserInfo,
            },
            {
                'field': 'facility',
                'serializer_class': FacilitySerializer,
            },
            {
                'field': 'message_for_day',
                'serializer_class': InfoMessageSerializer
            }
        ]


class PatientDiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientDiagnosis
        fields = '__all__'


class SimplifiedEmployeeProfileSerializer(RepresentationMixin, serializers.ModelSerializer):

    class Meta:
        model = EmployeeProfile
        fields = (
            'id',
            'user',
            'title',
        )
        read_only_fields = (
            'id',
        )
        nested_serializers = [
            {
                'field': 'user',
                'serializer_class': EmployeeUserInfo,
            },
            {
                'field': 'title',
                'serializer_class': ProviderTitleSerializer,
            },
        ]


class ProblemAreaSerializer(RepresentationMixin, serializers.ModelSerializer):
    class Meta:
        model = ProblemArea
        fields = (
            'id',
            'date_identified',
            'identified_by',
            'name',
            'description',
            'modified',
            'patient',
        )
        read_only_fields = (
            'id',
            'modified',
        )
        nested_serializers = [
            {
                'field': 'identified_by',
                'serializer_class': SimplifiedEmployeeProfileSerializer,
            },
            {
                'field': 'patient',
                'serializer_class': BasicPatientSerializer,
            },
        ]


class PatientProcedureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientProcedure
        fields = '__all__'


class PatientMedicationSerializer(RepresentationMixin,
                                  serializers.ModelSerializer):
    class Meta:
        model = PatientMedication
        fields = (
            'id',
            'patient',
            'medication',
            'dose_mg',
            'date_prescribed',
            'duration_days',
            'instructions',
            'prescribing_practitioner',
        )
        read_only_fields = (
            'id',
        )
        nested_serializers = [
            {
                'field': 'medication',
                'serializer_class': MedicationSerializer,
            },
            {
                'field': 'prescribing_practitioner',
                'serializer_class': SimplifiedEmployeeProfileSerializer,
            }
        ]


class PatientDashboardSerializer(serializers.ModelSerializer):

    task_percentage = serializers.SerializerMethodField()
    assessment_score = serializers.SerializerMethodField()
    tasks_today = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = (
            'id',
            'task_percentage',
            'assessment_score',
            'tasks_today',
        )
        read_only_fields = (
            'id',
        )

    def get_task_percentage(self, obj):
        from apps.tasks.utils import calculate_task_percentage
        return calculate_task_percentage(obj)

    def get_assessment_score(self, obj):
        now = timezone.now()
        past_30_days = now - relativedelta(days=30)
        responses = AssessmentResponse.objects.filter(
            assessment_task__appear_datetime__range=(past_30_days, now),
            assessment_task__plan__patient=obj,
            assessment_task__assessment_task_template__tracks_outcome=True
        )
        average = responses.aggregate(score=Avg('rating'))
        return round(average['score']) if average['score'] else 0

    def get_tasks_today(self, obj):
        from apps.tasks.utils import get_all_tasks_of_patient_today
        return get_all_tasks_of_patient_today(obj)


class PatientCarePlanSerializer(serializers.ModelSerializer):

    care_plans = serializers.SerializerMethodField()
    class Meta:
        model = PatientProfile
        fields = (
            'id',
            'care_plans',
        )
        read_only_fields = (
            'id',
        )

    def get_care_plans(self, obj):
        logger = logging.getLogger(__name__)
        logger.info("in PatientCarePlanSerialiser::get_care_plans obj = %s", obj)
        from apps.patients.utils import get_all_plans_for_patient
        return get_all_plans_for_patient(obj)

class PatientProfileSearchSerializer(HaystackSerializerMixin, PatientSearchSerializer):
    class Meta(PatientSearchSerializer.Meta):
        index_classes = [PatientProfileIndex]
        search_fields = ('text', )


class VerifiedUserSerializer(SettingsUserForSerializers,
                             serializers.ModelSerializer):
    token = serializers.SerializerMethodField()

    class Meta:
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'token',
        )

    def get_token(self, obj):
        token, created = Token.objects.get_or_create(user=obj)
        return token.key


class VerifiedPatientSerializer(serializers.ModelSerializer):
    """
    This serializer works in conjunction with `VerifyPatientSerializer`.
    This serializer will be used as representation after a patient
    gets verified.
    """
    user = VerifiedUserSerializer(read_only=True)

    class Meta:
        model = PatientProfile
        fields = (
            'id',
            'user',
            'is_active',
        )


class VerifyPatientSerializer(serializers.Serializer):
    """
    Serializer to be used for verifying a patient using the code
    """
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate_email(self, value):
        try:
            PatientProfile.objects.get(user__email=value)
        except PatientProfile.DoesNotExist:
            raise serializers.ValidationError(_('Given email does not exist.'))
        return value

    def validate(self, data):
        email = data.get('email')
        code = data.get('code')

        patient = PatientProfile.objects.get(user__email=email)

        try:
            PatientVerificationCode.objects.get(
                patient=patient,
                code=code
            )
        except PatientVerificationCode.DoesNotExist:
            raise serializers.ValidationError(
                _('The given email and code does not match any record in our '
                    'database.')
            )
        return data

    def save(self):
        email = self.validated_data.get('email')

        patient = PatientProfile.objects.get(user__email=email)
        patient.set_active()

    def to_representation(self, data):
        patient = PatientProfile.objects.get(user__email=data.get('email'))
        serializer = VerifiedPatientSerializer(patient)
        return serializer.data


class CreatePatientSerializer(serializers.Serializer):
    """
    Serializer for setting `preferred_name` and password for patients.
    """
    preferred_name = serializers.CharField(max_length=128, required=False)
    new_password1 = serializers.CharField(max_length=128)
    new_password2 = serializers.CharField(max_length=128)

    set_password_form_class = CustomSetPasswordForm

    def validate(self, attrs):
        self._errors = {}

        # Decode the uidb64 to uid to get User object
        request = self.context.get('request')

        # Construct SetPasswordForm instance
        self.set_password_form = self.set_password_form_class(
            user=request.user, data=attrs,
        )
        if not self.set_password_form.is_valid():
            raise serializers.ValidationError(self.set_password_form.errors)

        return attrs

    def save(self):
        return self.set_password_form.save()


class ReminderEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReminderEmail
        fields = [
            'patient',
            'subject',
            'message',
        ]


class PotentialPatientSerializer(serializers.ModelSerializer):

    class Meta:
        model = PotentialPatient
        fields = (
            'id',
            'first_name',
            'last_name',
            'care_plan',
            'phone',
            'facility',
            'patient_profile',
            'created',
            'modified',
        )
        read_only_fields = (
            'id',
            'created',
            'modified',
        )


class FacilityInactivePatientSerializer(serializers.ModelSerializer):
    """
    serializer to be used for inactive patients in a facility
    """
    full_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    care_plan = serializers.SerializerMethodField()
    care_manager = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = (
            'id',
            'full_name',
            'image_url',
            'care_plan',
            'last_app_use',
            'care_manager',
        )

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_image_url(self, obj):
        return obj.user.get_image_url()

    def get_care_plan(self, obj):
        latest_plan = obj.latest_care_plan
        return latest_plan.plan_template.name if latest_plan else ''

    def get_care_manager(self, obj):
        latest_plan = obj.latest_care_plan
        if latest_plan:
            manager = latest_plan.care_team_members.filter(
                is_manager=True).first()
            if manager:
                return manager.employee_profile.user.get_full_name()
        return ''


#BAM
class FacilityActivePatientSerializer(serializers.ModelSerializer):
    """
    serializer to be used for inactive patients in a facility
    """
    full_name = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    care_plan = serializers.SerializerMethodField()
    care_manager = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = (
            'id',
            'full_name',
            'image_url',
            'care_plan',
            'last_app_use',
            'care_manager',
        )

    def get_full_name(self, obj):
        return obj.user.get_full_name()

    def get_image_url(self, obj):
        return obj.user.get_image_url()

    def get_care_plan(self, obj):
        latest_plan = obj.latest_care_plan
        return latest_plan.plan_template.name if latest_plan else ''

    def get_care_manager(self, obj):
        latest_plan = obj.latest_care_plan
        if latest_plan:
            manager = latest_plan.care_team_members.filter(
                is_manager=True).first()
            if manager:
                return manager.employee_profile.user.get_full_name()
        return ''



class LatestPatientSymptomSerializer(serializers.ModelSerializer):
    """
    Serializer to be used for displaying latest symptom data per patient.
    """
    symptom = SymptomSerializer(read_only=True)
    behavior = serializers.SerializerMethodField()

    class Meta:
        model = SymptomRating
        fields = (
            'id',
            'symptom',
            'rating',
            'behavior',
            'created',
            'modified',
        )

    def get_behavior(self, obj):
        value = "increasing"
        second_rating = SymptomRating.objects.filter(
            symptom_task__plan__patient=obj.symptom_task.plan.patient,
            symptom=obj.symptom).exclude(id=obj.id).order_by(
            '-created').first()
        if second_rating:
            if obj.rating < second_rating.rating:
                value = "decreasing"
            elif obj.rating == second_rating.rating:
                value = "equal"
        return value
