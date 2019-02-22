from django.http import Http404
from django.utils.translation import ugettext_lazy as _

from rest_framework import serializers


class RepresentationMixin(object):
    """
    This mixin will handle representation of nested serializers. When used,
    `to_representation` method will require `nested_serializers` property
    in the serializer's Meta property. Below is an example:

        nested_serializers = [
            {
                'field': 'field_name',
                'serializer_class': ObjectSerializer,
                'many': True
            },
            {
                'another_field': 'field_name',
                'serializer_class': AnotherObjectSerializer,
                    'many': False  # False is default
            },
            ...
        ]
    """

    def to_representation(self, instance):
        data = super(RepresentationMixin, self).to_representation(instance)
        meta = getattr(self, 'Meta', None)
        nested_serializers = getattr(meta, 'nested_serializers', {})
        if nested_serializers:

            for obj in nested_serializers:
                field = obj.get('field')
                serializer_class = obj.get('serializer_class')
                many = obj.get('many', False)
                if getattr(instance, field, None):
                    serializer = serializer_class(
                        getattr(instance, field),
                        many=many,
                        context=self.context
                    )
                    data.update({
                        field: serializer.data
                    })

        return data


class ParentViewSetPermissionMixin(object):
    """
    This mixin will check for the user's access permission for the parent
    object in a nested ViewSet.
    """

    def filter_queryset_by_parents_lookups(self, queryset):
        parents_query_dict = self.get_parents_query_dict()
        parent_field = getattr(self, 'parent_field', None)
        skip_parent_permission_check = getattr(self,
                                               'skip_parent_permission_check',
                                               False)

        for field, model, viewset in self.parent_lookup:
            parent = model.objects.get(id=parents_query_dict[field])

            if not skip_parent_permission_check:
                viewset().check_object_permissions(self.request, parent)

            if field == parent_field:
                self.parent_obj = parent

        if parents_query_dict:
            try:
                return queryset.filter(**parents_query_dict)
            except ValueError:
                raise Http404
        else:
            return queryset


class ReferenceCheckMixin(object):
    """
    This mixin will validate the existence of custom foreign fields. When used,
    `validate` method will require `ref_validators` property
    in the serializer's Meta property. Below is an example:

        ref_validators = [
            {
                'field': 'care_manager',
                'model': EmployeeProfile
            },
            {
                'field': 'plan_template',
                'model': CarePlanTemplate
            },
            ...
        ]
    """

    def validate(self, data):
        super(ReferenceCheckMixin, self).validate(data)

        meta = getattr(self, 'Meta', None)
        ref_validators = getattr(meta, 'ref_validators', {})
        if ref_validators:
            for obj in ref_validators:
                field = obj.get('field')
                model = obj.get('model')
                value = data.get(field)
                if value:
                    if not model.objects.filter(pk=value):
                        raise serializers.ValidationError({ field: _('Given instance does not exist.')})

        return data
