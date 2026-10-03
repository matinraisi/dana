import django, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.schools.models import School
from django.contrib.auth import get_user_model
from apps.academy.models import Course, StudentEnrollment

User = get_user_model()

school, created = School.objects.get_or_create(
    slug='suntech',
    defaults={
        'title': 'آکادمی هوش مصنوعی سانتک',
        'is_active': True,
    }
)
if created:
    owner = User.objects.filter(is_superuser=True).first() or User.objects.first()
    school.owner = owner
    school.save()
    print(f'Created default school (id={school.id})')
else:
    print(f'Already exists (id={school.id})')

User.objects.filter(school__isnull=True).update(school_id=school.id)
Course.objects.filter(school__isnull=True).update(school_id=school.id)
StudentEnrollment.objects.filter(school__isnull=True).update(school_id=school.id)

print(f'Users assigned: {User.objects.filter(school=school).count()}')
print(f'Courses assigned: {Course.objects.filter(school=school).count()}')
print(f'Students assigned: {StudentEnrollment.objects.filter(school=school).count()}')
