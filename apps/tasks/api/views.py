from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import (
    PatientTaskTemplate,
    PatientTask,
    TeamTaskTemplate,
    TeamTask,
    MedicationTaskTemplate,
    MedicationTask,
    SymptomTaskTemplate,
    SymptomTask,
    SymptomRating,
    AssessmentTaskTemplate,
    AssessmentQuestion,
    AssessmentTask,
    AssessmentResponse,
)
from ..permissions import (
    IsPatientOrEmployeeForTask,
    IsPatientOrEmployeeReadOnly,
)
from ..utils import get_all_tasks_of_patient_today
from .filters import DurationFilter
from . serializers import (
    PatientTaskTemplateSerializer,
    PatientTaskSerializer,
    TeamTaskTemplateSerializer,
    TeamTaskSerializer,
    MedicationTaskTemplateSerializer,
    MedicationTaskSerializer,
    SymptomTaskTemplateSerializer,
    SymptomTaskSerializer,
    SymptomRatingSerializer,
    AssessmentTaskTemplateSerializer,
    AssessmentQuestionSerializer,
    AssessmentTaskSerializer,
    AssessmentResponseSerializer,
)
from care_adopt_backend import utils
from care_adopt_backend.permissions import (
    EmployeeOrReadOnly,
    IsPatientOnly,
)


class PatientTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = PatientTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = PatientTaskTemplate.objects.all()

    def get_queryset(self):
        qs = self.queryset
        employee_profile = utils.employee_profile_or_none(self.request.user)
        patient_profile = utils.patient_profile_or_none(self.request.user)

        if employee_profile is not None:
            # TODO: Only get task templates for patients this employee
            # has access to
            return qs.all()
        elif patient_profile is not None:
            patient_plans = patient_profile.care_plans.all()
            plan_templates = patient_plans.values_list("plan_template",
                                                       flat=True)
            return qs.filter(plan_template__id__in=plan_templates)
        else:
            return qs.none()


class PatientTaskViewSet(viewsets.ModelViewSet):
    serializer_class = PatientTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeForTask,
    )
    queryset = PatientTask.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'plan__id',
        'patient_task_template__id',
        'plan__patient__id',
        'status',
    )

    def get_queryset(self):
        queryset = super(PatientTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(plan__patient=user.patient_profile)

        return queryset


class TeamTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = TeamTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = TeamTaskTemplate.objects.all()


class TeamTaskViewSet(viewsets.ModelViewSet):
    serializer_class = TeamTaskSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = TeamTask.objects.all()


class MedicationTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = MedicationTaskTemplate.objects.all()


class MedicationTaskViewSet(viewsets.ModelViewSet):
    serializer_class = MedicationTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeForTask,
    )
    queryset = MedicationTask.objects.all()
    filter_backends = (DjangoFilterBackend, DurationFilter)
    filterset_fields = (
        'medication_task_template__plan__id',
        'medication_task_template__id',
        'medication_task_template__plan__patient__id',
        'status',
    )

    def get_queryset(self):
        queryset = super(MedicationTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                medication_task_template__plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(medication_task_template__plan__patient=user.patient_profile)

        return queryset


class SymptomTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = SymptomTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = SymptomTaskTemplate.objects.all()


class SymptomTaskViewSet(viewsets.ModelViewSet):
    serializer_class = SymptomTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeForTask,
    )
    queryset = SymptomTask.objects.all()
    filter_backends = (DjangoFilterBackend, DurationFilter)
    filterset_fields = (
        'plan__id',
        'symptom_task_template__id',
        'plan__patient__id',
    )

    def get_queryset(self):
        queryset = super(SymptomTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(plan__patient=user.patient_profile)

        return queryset


class SymptomRatingViewSet(viewsets.ModelViewSet):
    serializer_class = SymptomRatingSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeReadOnly,
    )
    queryset = SymptomRating.objects.all()


class AssessmentTaskTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentTaskTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = AssessmentTaskTemplate.objects.all()


class AssessmentQuestionViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentQuestionSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = AssessmentQuestion.objects.all()


class AssessmentTaskViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentTaskSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeForTask,
    )
    queryset = AssessmentTask.objects.all()
    filter_backends = (DjangoFilterBackend, DurationFilter)
    filterset_fields = (
        'plan__id',
        'assessment_task_template__id',
        'plan__patient__id',
    )

    def get_queryset(self):
        queryset = super(AssessmentTaskViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(plan__patient=user.patient_profile)

        return queryset


class AssessmentResponseViewSet(viewsets.ModelViewSet):
    serializer_class = AssessmentResponseSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsPatientOrEmployeeReadOnly,
    )
    queryset = AssessmentResponse.objects.all()
    filter_backends = (DjangoFilterBackend, )
    filterset_fields = (
        'assessment_task__id',
        'assessment_question__id',
    )

    def get_queryset(self):
        queryset = super(AssessmentResponseViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                assessment_task__plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(
                assessment_task__plan__patient=user.patient_profile
            )

        return queryset


############################
# ----- CUSTOM VIEWS ----- #
############################

class TodaysTasksAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated, IsPatientOnly)

    def get(self, request, format=None):
        tasks = get_all_tasks_of_patient_today(request.user.patient_profile)
        return Response(data=tasks)
