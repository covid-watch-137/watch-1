from rest_framework import serializers

from ..models import BilledActivity
from apps.core.api.mixins import RepresentationMixin
from apps.core.api.serializers import BasicEmployeeProfileSerializer
from apps.plans.api.serializers import CarePlanSerializer


class BilledActivitySerializer(RepresentationMixin,
                               serializers.ModelSerializer):
    """
    serializer for :model:`billings.BilledActivity`
    """

    class Meta:
        model = BilledActivity
        fields = (
            'id',
            'plan',
            'activity_type',
            'members',
            'sync_to_ehr',
            'added_by',
            'activity_date',
            'notes',
            'time_spent',
            'readable_time_spent',
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
                'field': 'plan',
                'serializer_class': CarePlanSerializer,
            },
            {
                'field': 'members',
                'serializer_class': BasicEmployeeProfileSerializer,
            },
            {
                'field': 'added_by',
                'serializer_class': BasicEmployeeProfileSerializer
            }
        ]
