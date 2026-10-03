from .models import School


def school_context(request):
    school = getattr(request, 'school', None)
    if school is None and request.user.is_authenticated:
        school_id = getattr(request.user, 'school_id', None)
        if school_id:
            try:
                school = School.objects.get(id=school_id, is_active=True)
            except School.DoesNotExist:
                school = None
    if school is None:
        try:
            school = School.objects.filter(is_default=True, is_active=True).first()
        except Exception:
            school = None
    return {
        'school': school,
        'school_title': school.title if school else 'آکادمی هوش مصنوعی سانتک',
        'school_logo': school.logo.url if school and school.logo else None,
        'school_favicon': school.favicon.url if school and school.favicon else None,
        'school_color': school.primary_color if school else '#2563eb',
    }
