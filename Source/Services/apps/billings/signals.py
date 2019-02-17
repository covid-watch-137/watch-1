def billedactivity_post_save(sender, instance, created, **kwargs):
    """
    Function to be used as signal (post_save) when saving
    :model:`billings.BilledActivity`
    """
    plan = instance.plan
    if instance.is_billed:
        unbilled_activities = plan.activities.filter(is_billed=False)
        if not unbilled_activities.exists() and not plan.is_billed:
            plan.is_billed = True
            plan.save(update_fields=['is_billed'])
    elif plan.is_billed:
        plan.is_billed = False
        plan.save(update_fields=['is_billed'])
