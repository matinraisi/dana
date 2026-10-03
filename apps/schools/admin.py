from django.contrib import admin
from .models import School
from apps.notifications.sms import send_sms


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ('title', 'subdomain', 'domain', 'owner', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'subdomain', 'domain', 'owner__username')
    readonly_fields = ('slug', 'created_at', 'updated_at')
    fieldsets = (
        ('مشخصات آموزشگاه', {
            'fields': ('title', 'slug', 'subdomain', 'domain', 'is_active', 'is_default')
        }),
        ('برندینگ', {
            'fields': ('logo', 'favicon', 'primary_color')
        }),
        ('اطلاعات تماس', {
            'fields': ('phone', 'email', 'address', 'description')
        }),
        ('مدیریت', {
            'fields': ('owner',)
        }),
        ('زمان', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = self.model.objects.get(pk=obj.pk)
            was_inactive = not old_obj.is_active
        else:
            was_inactive = False

        super().save_model(request, obj, form, change)

        # مطمئن شو owner.school ست شده
        if obj.owner and obj.owner.school_id != obj.id:
            obj.owner.school = obj
            obj.owner.save(update_fields=['school'])

        if was_inactive and obj.is_active and obj.owner.phone_number:
            msg = (
                f"آموزشگاه شما با نام «{obj.title}» تأیید شد.\n"
                f"با نام کاربری {obj.owner.username} و رمز عبور خود وارد شوید."
            )
            send_sms(obj.owner.phone_number, msg)
