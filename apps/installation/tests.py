from django.test import TestCase
from .models import InstallationConfig


class InstallationConfigTests(TestCase):
    def test_singleton_creation(self):
        """Test 1: InstallationConfig.get_solo() creates one configuration with pk == 1."""
        config = InstallationConfig.get_solo()
        self.assertIsNotNone(config)
        self.assertEqual(config.pk, 1)
        self.assertEqual(InstallationConfig.objects.count(), 1)

    def test_get_solo_returns_same_object(self):
        """Test 2: Multiple get_solo() calls return the same object without creating duplicates."""
        first = InstallationConfig.get_solo()
        second = InstallationConfig.get_solo()
        self.assertEqual(first.pk, 1)
        self.assertEqual(second.pk, 1)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(InstallationConfig.objects.count(), 1)

    def test_save_forces_pk_one(self):
        """Test 3: Saving an object with any pk forces pk=1 and avoids duplicate records."""
        custom_config = InstallationConfig(
            pk=99,
            organization_name="Custom Academy",
        )
        custom_config.save()
        self.assertEqual(custom_config.pk, 1)
        self.assertEqual(InstallationConfig.objects.count(), 1)

        fetched = InstallationConfig.objects.get(pk=1)
        self.assertEqual(fetched.organization_name, "Custom Academy")

    def test_required_defaults(self):
        """Test 4: A fresh singleton has the expected default attributes."""
        config = InstallationConfig.get_solo()
        self.assertEqual(config.organization_name, "AI House EDU")
        self.assertEqual(config.primary_color, "#4f46e5")
        self.assertEqual(config.secondary_color, "#06b6d4")
