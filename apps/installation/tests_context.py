from django.test import TestCase, RequestFactory
from django.template import Template, Context
from .models import InstallationConfig
from .context_processors import installation
from .utils import get_installation_config


class InstallationContextProcessorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        InstallationConfig.objects.all().delete()

    def test_context_processor_returns_installation(self):
        """Test 1: Context contains installation object with expected fields."""
        config = InstallationConfig.get_solo()
        config.organization_name = "Test Academy EDU"
        config.save()

        request = self.factory.get('/')
        ctx = installation(request)

        self.assertIn('installation', ctx)
        self.assertEqual(ctx['installation'].organization_name, "Test Academy EDU")

    def test_template_rendering_with_context_processor(self):
        """Test 2: Templates can access installation attributes via context processor."""
        config = InstallationConfig.get_solo()
        config.organization_name = "Rendered Academy"
        config.primary_color = "#10b981"
        config.save()

        request = self.factory.get('/')
        # Simulate rendering with context processor dict
        template = Template("Welcome to {{ installation.organization_name }} with color {{ installation.primary_color }}")
        context = Context({**installation(request)})
        rendered = template.render(context)

        self.assertIn("Welcome to Rendered Academy", rendered)
        self.assertIn("#10b981", rendered)

    def test_utils_get_installation_config(self):
        """Test 3: get_installation_config helper returns singleton consistently."""
        c1 = get_installation_config()
        c2 = get_installation_config()
        self.assertEqual(c1.pk, 1)
        self.assertEqual(c1, c2)
        self.assertEqual(InstallationConfig.objects.count(), 1)
