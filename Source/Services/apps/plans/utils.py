import pytz

from datetime import datetime, time

from dateutil import rrule
from dateutil.relativedelta import relativedelta

from django.utils import timezone
from rest_framework import serializers


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        # Check if this is a base64 string
        if isinstance(data, six.string_types):
            # Check if the base64 string is in the "data:" format
            if 'data:' in data and ';base64,' in data:
                # Break out the header from the base64 content
                header, data = data.split(';base64,')

            # Try to decode the file. Return validation error if it fails.
            try:
                decoded_file = base64.b64decode(data)
            except TypeError:
                self.fail('invalid_image')

            # Generate file name:
            file_name = str(uuid.uuid4())[:12] # 12 characters are more than enough.
            # Get the file name extension:
            file_extension = self.get_file_extension(file_name, decoded_file)

            complete_file_name = "%s.%s" % (file_name, file_extension, )

            data = ContentFile(decoded_file, name=complete_file_name)

        return super(Base64ImageField, self).to_internal_value(data)

    def get_file_extension(self, file_name, decoded_file):
        extension = imghdr.what(file_name, decoded_file)
        extension = "jpg" if extension == "jpeg" else extension
        return extension


def replace_time(datetime_obj, time_obj):
    return datetime_obj.replace(
        hour=time_obj.hour,
        minute=time_obj.minute,
        second=time_obj.second
    )


def add_days_and_replace_time(datetime_obj, days, time_obj):
    new_datetime = datetime_obj + relativedelta(days=days)
    new_datetime = replace_time(new_datetime, time_obj)
    return new_datetime


def create_tasks_from_template(template,
                               duration_weeks,
                               instance_model,
                               template_config={},
                               task_template=None):

    # for ongoing plans (duration_weeks = -1), set it as 3 years
    duration_weeks = 157 if duration_weeks == -1 else duration_weeks
    date_end = timezone.now() + relativedelta(weeks=duration_weeks)
    plan_end = datetime.combine(date_end.date(), time.max, tzinfo=pytz.utc)

    template = task_template if task_template else template

    due_datetime = add_days_and_replace_time(
        timezone.now(),
        template.start_on_day,
        template.due_time
    )
    appear_datetime = add_days_and_replace_time(
        timezone.now(),
        template.start_on_day,
        template.appear_time
    )

    if template.frequency == 'daily':

        if template.repeat_amount > 0:

            # Gets all dates from due_datetime up to the
            # number of `count` given. In this case, that would be the
            # `template.repeat_amount`
            due_dates = rrule.rrule(
                rrule.DAILY,
                dtstart=due_datetime,
                count=template.repeat_amount,
            )

            # Gets all dates from appear_datetime up to the
            # number of `count` given. In this case, that would be the
            # `template.repeat_amount`
            appear_dates = rrule.rrule(
                rrule.DAILY,
                dtstart=appear_datetime,
                count=template.repeat_amount,
            )

        else:
            # Gets all dates from due_datetime to plan_end
            due_dates = rrule.rrule(
                rrule.DAILY,
                dtstart=due_datetime,
                until=plan_end,
            )

            # Gets all dates from appear_datetime to plan_end
            appear_dates = rrule.rrule(
                rrule.DAILY,
                dtstart=appear_datetime,
                until=plan_end,
            )

    elif template.frequency == 'weekly':

        if template.repeat_amount > 0:
            # Gets all dates weekly from due_datetime up to the
            # number of `count` given. In this case, that would be the
            # `template.repeat_amount`
            due_dates = rrule.rrule(
                rrule.WEEKLY,
                dtstart=due_datetime,
                count=template.repeat_amount,
            )

            # Gets all dates weekly from appear_datetime up to the
            # number of `count` given. In this case, that would be the
            # `template.repeat_amount`
            appear_dates = rrule.rrule(
                rrule.WEEKLY,
                dtstart=appear_datetime,
                count=template.repeat_amount,
            )

        else:
            # Gets all dates weekly from due_datetime to plan_end
            due_dates = rrule.rrule(
                rrule.WEEKLY,
                dtstart=due_datetime,
                until=plan_end,
            )

            # Gets all dates weekly from appear_datetime to plan_end
            appear_dates = rrule.rrule(
                rrule.WEEKLY,
                dtstart=appear_datetime,
                until=plan_end,
            )

    elif template.frequency == 'every_other_day':

        if template.repeat_amount > 0:

            due_dates = rrule.rrule(
                rrule.DAILY,
                interval=2,
                dtstart=due_datetime,
                count=template.repeat_amount,
            )

            appear_dates = rrule.rrule(
                rrule.DAILY,
                interval=2,
                dtstart=appear_datetime,
                count=template.repeat_amount,
            )

        else:
            due_dates = rrule.rrule(
                rrule.DAILY,
                interval=2,
                dtstart=due_datetime,
                until=plan_end,
            )

            appear_dates = rrule.rrule(
                rrule.DAILY,
                interval=2,
                dtstart=appear_datetime,
                until=plan_end,
            )

    elif template.frequency == 'weekdays' or \
            template.frequency == 'weekends':

        days_lookup = {
            'weekdays': [0, 1, 2, 3, 4],  # Monday-Friday
            'weekends': [5, 6]  # Saturday-Sunday
        }

        if template.repeat_amount > 0:
            # Gets all weekday/weekend dates from due_datetime up to the
            # number of `count` given. In this case, that would be the
            # `template.repeat_amount`
            due_dates = rrule.rrule(
                rrule.DAILY,
                dtstart=due_datetime,
                count=template.repeat_amount,
                byweekday=days_lookup[template.frequency]
            )

            # Gets all weekday/weekend dates from appear_datetime up to the
            # number of `count` given. In this case, that would be the
            # `template.repeat_amount`
            appear_dates = rrule.rrule(
                rrule.DAILY,
                dtstart=appear_datetime,
                count=template.repeat_amount,
                byweekday=days_lookup[template.frequency]
            )

        else:
            # Create tasks on all weekends or weekdays until plan ends.

            # Gets all weekday/weekend dates from due_datetime to plan_end
            due_dates = rrule.rrule(
                rrule.DAILY,
                dtstart=due_datetime,
                until=plan_end,
                byweekday=days_lookup[template.frequency]
            )

            # Gets all weekday/weekend dates from appear_datetime to
            # plan_end
            appear_dates = rrule.rrule(
                rrule.DAILY,
                dtstart=appear_datetime,
                until=plan_end,
                byweekday=days_lookup[template.frequency]
            )

    if template.frequency == 'once':
        instance_model.objects.create(
            due_datetime=due_datetime,
            appear_datetime=appear_datetime,
            **template_config)
    elif appear_dates.count() > 0 and due_dates.count() > 0:
        dates = zip(list(appear_dates), list(due_dates))

        for appear, due in dates:
            instance_model.objects.create(
                due_datetime=due,
                appear_datetime=appear,
                **template_config)


def duplicate_tasks(queryset, new_plan_template, question_field=None):
    for ii in queryset:
        if question_field:
            qs = ii.questions.all()

        ii.pk = None
        ii.plan_template = new_plan_template
        ii.save()

        if question_field:
            for question in qs:
                question.pk = None
                setattr(question, question_field, ii)
                question.save()
