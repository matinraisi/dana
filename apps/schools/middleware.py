from .models import School


class SchoolMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            host = request.META.get('HTTP_HOST', '')
            host = host.split(':')[0]

            school = None
            try:
                school = School.objects.get(domain=host, is_active=True)
            except School.DoesNotExist:
                parts = host.split('.')
                if len(parts) >= 3 or host.endswith('.localhost'):
                    prefix = parts[0]
                    try:
                        school = School.objects.get(subdomain=prefix, is_active=True)
                    except School.DoesNotExist:
                        pass

            request.school = school
        except Exception:
            request.school = None

        return self.get_response(request)
