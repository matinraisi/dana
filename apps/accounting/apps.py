from django.apps import AppConfig


class AccountingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounting'
    verbose_name = 'حسابداری'

    def ready(self):
        # این خط باعث می‌شود سیگنال‌ها هنگام بالا آمدن پروژه لود شوند
        import apps.accounting.signals