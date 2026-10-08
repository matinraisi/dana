from django.db import migrations, models


# (app_label, model_name, fk_field) that pointed at schools.School
_SCHOOL_FK_TARGETS = [
    ('academy', 'Course', 'school_id'),
    ('academy', 'StudentEnrollment', 'school_id'),
    ('academy', 'SMSLog', 'school_id'),
    ('academy', 'ExpenseCategory', 'school_id'),
    ('academy', 'PaymentGateway', 'school_id'),
    ('academy', 'DiscountCode', 'school_id'),
    ('academy', 'OrganizationMembership', 'organization_id'),
    ('crm', 'Lead', 'school_id'),
]


def _pick_primary(School):
    primary = School.objects.filter(is_default=True, is_active=True).first()
    if primary:
        return primary
    primary = School.objects.filter(is_active=True).order_by('id').first()
    if primary:
        return primary
    return School.objects.order_by('id').first()


def consolidate_to_singleton(apps, schema_editor):
    """Merge multi-tenant School rows into one Academy Organization.

    Primary selection: is_default+active, else first active, else lowest id.
    Related rows are reassigned; secondary School rows are deleted.
    """
    School = apps.get_model('schools', 'School')
    primary = _pick_primary(School)
    if primary is None:
        return

    secondary = list(School.objects.exclude(pk=primary.pk))
    if not secondary:
        School.objects.filter(pk=primary.pk).update(is_active=True, is_default=True)
        return

    secondary_ids = [s.pk for s in secondary]

    for app_label, model_name, fk_field in _SCHOOL_FK_TARGETS:
        try:
            Model = apps.get_model(app_label, model_name)
        except LookupError:
            continue
        Model.objects.filter(**{f'{fk_field}__in': secondary_ids}).update(
            **{fk_field: primary.pk}
        )

    # Membership is OneToOne(user); after reassignment, collapse duplicates if any.
    try:
        Membership = apps.get_model('academy', 'OrganizationMembership')
        seen_users = set()
        for membership in Membership.objects.filter(organization_id=primary.pk).order_by('id'):
            if membership.user_id in seen_users:
                membership.delete()
            else:
                seen_users.add(membership.user_id)
    except LookupError:
        pass

    School.objects.filter(pk__in=secondary_ids).delete()
    School.objects.filter(pk=primary.pk).update(is_active=True, is_default=True)


def noop_reverse(apps, schema_editor):
    # Irreversible consolidation — secondary orgs cannot be reconstructed.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0002_school_add_is_default'),
        ('academy', '0026_claim_teacher_studentaccount'),
        # crm may not be loaded yet during graph build on some paths; keep soft order:
        ('crm', '0002_lead_school'),
        ('users', '0002_otptoken'),
    ]

    operations = [
        migrations.RunPython(consolidate_to_singleton, noop_reverse),
        migrations.RemoveField(model_name='school', name='subdomain'),
        migrations.RemoveField(model_name='school', name='domain'),
        migrations.RemoveField(model_name='school', name='is_default'),
        migrations.AlterModelOptions(
            name='school',
            options={
                'ordering': ['-created_at'],
                'verbose_name': 'سازمان آموزشگاه',
                'verbose_name_plural': 'سازمان آموزشگاه',
            },
        ),
        migrations.AlterField(
            model_name='school',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='فعال'),
        ),
        migrations.AlterField(
            model_name='school',
            name='title',
            field=models.CharField(max_length=255, verbose_name='نام سازمان آموزشگاه'),
        ),
    ]
