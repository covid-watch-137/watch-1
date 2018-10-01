from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.generics import RetrieveAPIView
from rest_framework.response import Response

from ..models import (
    CarePlanTemplate,
    CarePlan,
    PlanConsent,
    GoalTemplate,
    Goal,
    GoalProgress,
    GoalComment,
    InfoMessageQueue,
    InfoMessage,
    CareTeamMember,
)
from .serializers import (
    CarePlanTemplateSerializer,
    CarePlanSerializer,
    PlanConsentSerializer,
    CareTeamMemberSerializer,
    GoalTemplateSerializer,
    GoalSerializer,
    GoalProgressSerializer,
    GoalCommentSerializer,
    InfoMessageQueueSerializer,
    InfoMessageSerializer,
)
from apps.core.models import ProviderRole
from apps.core.api.serializers import ProviderRoleSerializer
from apps.tasks.permissions import IsEmployeeOrPatientReadOnly
from care_adopt_backend import utils
from care_adopt_backend.permissions import EmployeeOrReadOnly
from django.utils import timezone


class CarePlanTemplateViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`plans.CarePlanTemplate`
    ========

    create:
        Creates :model:`plans.CarePlanTemplate` object.
        Only admins and employees are allowed to perform this action.

    update:
        Updates :model:`plans.CarePlanTemplate` object.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.

    partial_update:
        Updates one or more fields of an existing plan template object.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.

    retrieve:
        Retrieves a :model:`plans.CarePlanTemplate` instance.
        Admins will have access to all plan template objects. Employees will
        only have access to those plan templates belonging to its own care
        team. Patients will have access to all plan templates assigned to them.

    list:
        Returns list of all :model:`plans.CarePlanTemplate` objects.
        Admins will get all existing plan template objects. Employees will get
        the plan templates belonging to a certain care team. Patients will get
        all plan templates belonging to them.

    delete:
        Deletes a :model:`plans.CarePlanTemplate` instance.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.
    """
    serializer_class = CarePlanTemplateSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )
    queryset = CarePlanTemplate.objects.all()

    def get_queryset(self):
        queryset = super(CarePlanTemplateViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            # TODO: Move this to django filtering
            exclude_inactive = self.request.query_params.get('exclude_inactive')
            if exclude_inactive == "true":
                queryset = queryset.exclude(is_active=False)
        elif user.is_patient:
            queryset = queryset.filter(
                care_plans__patient=user.patient_profile,
                is_active=True
            )

        return queryset


class CarePlanViewSet(viewsets.ModelViewSet):
    """
    Permissions
    ========
    Employees get all care plans, patients only get the ones they're
    assigned to.
    """
    serializer_class = CarePlanSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_queryset(self):
        qs = CarePlan.objects.all()
        employee_profile = utils.employee_profile_or_none(self.request.user)
        patient_profile = utils.patient_profile_or_none(self.request.user)
        if employee_profile is not None:
            return qs.all()
        if patient_profile is not None:
            return patient_profile.care_plans.all()
        return CarePlan.objects.none()

    @action(methods=['get'], detail=True)
    def care_team_members(self, request, pk=None):
        plan = CarePlan.objects.get(id=pk)
        care_team_members = plan.care_team_members
        serializer = CareTeamMemberSerializer(care_team_members, many=True)
        return Response(serializer.data)

    @action(methods=['get'], detail=True)
    def available_roles(self, request, pk=None):
        plan = CarePlan.objects.get(id=pk)
        template = plan.plan_template
        care_team_members = plan.care_team_members
        all_roles = list(template.team_tasks.filter(
            role__isnull=False).values_list('role', flat=True).distinct())
        assigned_roles = list(care_team_members.filter(
                role__isnull=False).values_list('role', flat=True).distinct())
        available_roles = ProviderRole.objects.filter(
            id__in=list(set(all_roles) - set(assigned_roles)))
        serializer = ProviderRoleSerializer(available_roles, many=True)
        return Response(serializer.data)


class PlanConsentViewSet(viewsets.ModelViewSet):
    """
    Permissions
    ========
    Employees get all consent forms, patients only get their own.
    """
    serializer_class = PlanConsentSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )

    def get_queryset(self):
        qs = PlanConsent.objects.all()
        employee_profile = utils.employee_profile_or_none(self.request.user)
        patient_profile = utils.patient_profile_or_none(self.request.user)
        if employee_profile is not None:
            return qs.all()
        if patient_profile is not None:
            return qs.filter(plan__in=patient_profile.care_plans.all())
        return PlanConsent.objects.none()


class CareTeamMemberViewSet(viewsets.ModelViewSet):
    serializer_class = CareTeamMemberSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )

    def get_queryset(self):
        qs = CareTeamMember.objects.all()

        plan = self.request.query_params.get('plan')
        if plan:
            qs = qs.filter(plan=plan)
        employee_param = self.request.query_params.get('employee')
        if employee_param:
            qs = qs.filter(employee_profile=employee_param)

        employee_profile = utils.employee_profile_or_none(self.request.user)
        patient_profile = utils.patient_profile_or_none(self.request.user)
        if employee_profile is not None:
            qs = qs.all()
        elif patient_profile is not None:
            qs = qs.filter(plan__patient=patient_profile)
        else:
            return qs.none()
        return qs


class GoalTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = GoalTemplateSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = GoalTemplate.objects.all()


class GoalViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`plans.Goal`
    ========

    create:
        Creates :model:`plans.Goal` object.
        Only admins and employees are allowed to perform this action.

    update:
        Updates :model:`plans.Goal` object.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.

    partial_update:
        Updates one or more fields of an existing goal object.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.

    retrieve:
        Retrieves a :model:`plans.Goal` instance.
        Admins will have access to all goal objects. Employees will only have
        access to those goals belonging to its own care team. Patients will
        have access to all goals assigned to them.

    list:
        Returns list of all :model:`plans.Goal` objects.
        Admins will get all existing goal objects. Employees will get the goals
        belonging to a certain care team. Patients will get all goals belonging
        to them.

    delete:
        Deletes a :model:`plans.Goal` instance.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.
    """
    serializer_class = GoalSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )
    queryset = Goal.objects.all()

    def get_queryset(self):
        queryset = super(GoalViewSet, self).get_queryset()
        user = self.request.user
        include_future_goals = self.request.query_params.get('include_future_goals')

        if not include_future_goals:
            queryset = queryset.exclude(start_on_datetime__gte=timezone.now())

        if user.is_employee:
            queryset = queryset.filter(
                plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(plan__patient=user.patient_profile)

        return queryset


class GoalProgressViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`plans.GoalProgress`
    ========

    create:
        Creates :model:`plans.GoalProgress` object.
        Only admins and employees are allowed to perform this action.

    update:
        Updates :model:`plans.GoalProgress` object.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.

    partial_update:
        Updates one or more fields of an existing goal object.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.

    retrieve:
        Retrieves a :model:`plans.GoalProgress` instance.
        Admins will have access to all goal progress objects. Employees will
        only have access to those progresses belonging to its own care team.
        Patients will have access to all progresses assigned to them.

    list:
        Returns list of all :model:`plans.GoalProgress` objects.
        Admins will get all existing goal progress objects. Employees will get
        the progress belonging to a certain care team. Patients will get all
        progresses belonging to them.

    delete:
        Deletes a :model:`plans.GoalProgress` instance.
        Only admins and employees who belong to the same care team are allowed
        to perform this action.
    """
    serializer_class = GoalProgressSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )
    queryset = GoalProgress.objects.all()

    def get_queryset(self):
        queryset = super(GoalProgressViewSet, self).get_queryset()
        user = self.request.user

        if user.is_employee:
            queryset = queryset.filter(
                goal__plan__care_team_members__employee_profile=user.employee_profile
            )
        elif user.is_patient:
            queryset = queryset.filter(
                goal__plan__patient=user.patient_profile
            )

        return queryset


class GoalCommentViewSet(viewsets.ModelViewSet):
    """
    Viewset for :model:`plans.GoalComment`
    ========

    create:
        Creates :model:`plans.GoalComment` object.
        All authenticated users are allowed to perform this action.

    update:
        Updates :model:`plans.GoalComment` object.
        All authenticated users are allowed to perform this action so long as
        the comment belongs to them.

    partial_update:
        Updates one or more fields of an existing goal comment object.
        All authenticated users are allowed to perform this action so long as
        the comment belongs to them.

    retrieve:
        Retrieves a :model:`plans.GoalComment` instance.
        Admins will have access to all goal comment objects while employees and
        patients will only have access to comments they own.

    list:
        Returns list of all :model:`plans.GoalComment` objects.
        Admins will have access to all goal comment objects while employees and
        patients will only have access to comments they own.

    delete:
        Deletes a :model:`plans.GoalComment` instance.
        Admins will have access to all goal comment objects while employees and
        patients will only have access to comments they own.
    """
    serializer_class = GoalCommentSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )
    queryset = GoalComment.objects.all()

    def get_queryset(self):
        queryset = super(GoalCommentViewSet, self).get_queryset()
        user = self.request.user

        if not user.is_superuser:
            queryset = queryset.filter(user=user)

        return queryset


class InfoMessageQueueViewSet(viewsets.ModelViewSet):
    serializer_class = InfoMessageQueueSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = InfoMessageQueue.objects.all()


class InfoMessageViewSet(viewsets.ModelViewSet):
    serializer_class = InfoMessageSerializer
    permission_classes = (permissions.IsAuthenticated, EmployeeOrReadOnly, )
    queryset = InfoMessage.objects.all()


############################
# ----- CUSTOM VIEWS ----- #
############################

class GoalTemplatesByPlanTemplate(RetrieveAPIView):
    """
    Returns a list of goal templates related to the given plan template.
    """
    queryset = CarePlanTemplate.objects.all()
    serializer_class = GoalTemplateSerializer
    permission_classes = (
        permissions.IsAuthenticated,
        IsEmployeeOrPatientReadOnly,
    )

    def get_queryset(self):
        queryset = super(GoalTemplatesByPlanTemplate, self).get_queryset()
        user = self.request.user

        if user.is_patient:
            queryset = queryset.filter(
                care_plans__patient=user.patient_profile
            )

        return queryset

    def get_goal_templates(self):
        instance = self.get_object()
        return instance.goals.all()

    def retrieve(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_goal_templates())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
