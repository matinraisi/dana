from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from apps.academy.mixins import AdminRequiredMixin
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.utils.text import slugify

from .models import DynamicForm, FormField, FormSubmission, FieldResponse


class FormListView(AdminRequiredMixin, View):
    def get(self, request):
        forms = DynamicForm.objects.filter(created_by=request.user).order_by('-created_at')
        return render(request, 'forms_builder/form_list.html', {'forms': forms})


class FormCreateView(AdminRequiredMixin, View):
    def get(self, request):
        from apps.academy.models import Course
        courses = Course.objects.filter(is_active=True)
        return render(request, 'forms_builder/form_create.html', {'courses': courses})

    def post(self, request):
        title = request.POST.get('title', '').strip()
        if not title:
            messages.error(request, 'عنوان فرم الزامی است.')
            return redirect('forms_builder:form_create')

        slug = slugify(title, allow_unicode=True)
        base_slug = slug
        counter = 1
        while DynamicForm.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        form_obj = DynamicForm.objects.create(
            title=title,
            slug=slug,
            description=request.POST.get('description', ''),
            is_public=request.POST.get('is_public') == 'on',
            requires_login=request.POST.get('requires_login') == 'on',
            one_response_per_user=request.POST.get('one_response_per_user') == 'on',
            submit_message=request.POST.get('submit_message', 'پاسخ شما ثبت شد.'),
            linked_course_id=request.POST.get('linked_course') or None,
            created_by=request.user,
        )
        messages.success(request, f'فرم «{title}» ایجاد شد.')
        return redirect('forms_builder:form_builder', pk=form_obj.pk)


class FormBuilderView(AdminRequiredMixin, View):
    def get(self, request, pk):
        form_obj = get_object_or_404(DynamicForm, pk=pk, created_by=request.user)
        return render(request, 'forms_builder/form_builder.html', {
            'form_obj': form_obj,
            'field_types': FormField.FIELD_TYPES,
        })

    def post(self, request, pk):
        form_obj = get_object_or_404(DynamicForm, pk=pk, created_by=request.user)
        action = request.POST.get('action')

        if action == 'add_field':
            field_type = request.POST.get('field_type', 'text')
            label = request.POST.get('label', '').strip()
            if not label:
                messages.error(request, 'برچسب فیلد الزامی است.')
                return redirect('forms_builder:form_builder', pk=pk)

            last_order = form_obj.fields.order_by('-order').values_list('order', flat=True).first() or 0
            FormField.objects.create(
                form=form_obj,
                field_type=field_type,
                label=label,
                placeholder=request.POST.get('placeholder', ''),
                help_text=request.POST.get('help_text', ''),
                is_required=request.POST.get('is_required') == 'on',
                options=request.POST.get('options', ''),
                order=last_order + 1,
            )
            messages.success(request, 'فیلد اضافه شد.')

        elif action == 'delete_field':
            field_id = request.POST.get('field_id')
            FormField.objects.filter(pk=field_id, form=form_obj).delete()

        elif action == 'reorder':
            for key, value in request.POST.items():
                if key.startswith('order_'):
                    field_id = key.replace('order_', '')
                    try:
                        FormField.objects.filter(pk=field_id, form=form_obj).update(order=int(value))
                    except (ValueError, TypeError):
                        pass

        return redirect('forms_builder:form_builder', pk=pk)


class FormPublicView(View):
    def get(self, request, slug):
        try:
            form_obj = DynamicForm.objects.get(slug=slug, is_active=True)
        except DynamicForm.DoesNotExist:
            return render(request, 'forms_builder/form_not_found.html', {'slug': slug}, status=404)

        if form_obj.requires_login and not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')

        if form_obj.one_response_per_user and request.user.is_authenticated:
            already = FormSubmission.objects.filter(form=form_obj, submitted_by=request.user).exists()
            if already:
                return render(request, 'forms_builder/already_submitted.html', {'form_obj': form_obj})

        return render(request, 'forms_builder/form_public.html', {
            'form_obj': form_obj,
            'fields': form_obj.fields.order_by('order'),
        })

    def post(self, request, slug):
        try:
            form_obj = DynamicForm.objects.get(slug=slug, is_active=True)
        except DynamicForm.DoesNotExist:
            return render(request, 'forms_builder/form_not_found.html', {'slug': slug}, status=404)

        if form_obj.requires_login and not request.user.is_authenticated:
            return redirect(f'/login/?next={request.path}')

        submission = FormSubmission.objects.create(
            form=form_obj,
            submitted_by=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        for field in form_obj.fields.order_by('order'):
            if field.field_type in ('heading', 'paragraph'):
                continue
            if field.field_type == 'checkbox':
                value = ', '.join(request.POST.getlist(f'field_{field.pk}'))
            elif field.field_type == 'file':
                file_obj = request.FILES.get(f'field_{field.pk}')
                FieldResponse.objects.create(
                    submission=submission,
                    field=field,
                    value='',
                    file_upload=file_obj,
                )
                continue
            else:
                value = request.POST.get(f'field_{field.pk}', '')

            FieldResponse.objects.create(
                submission=submission,
                field=field,
                value=value,
            )

        return render(request, 'forms_builder/form_submitted.html', {'form_obj': form_obj})


class FormResponsesView(AdminRequiredMixin, View):
    def get(self, request, pk):
        form_obj = get_object_or_404(DynamicForm, pk=pk, created_by=request.user)
        submissions = form_obj.submissions.prefetch_related('responses__field').order_by('-submitted_at')
        fields = form_obj.fields.order_by('order').exclude(field_type__in=['heading', 'paragraph'])
        return render(request, 'forms_builder/form_responses.html', {
            'form_obj': form_obj,
            'submissions': submissions,
            'fields': fields,
        })


class FormDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        form_obj = get_object_or_404(DynamicForm, pk=pk, created_by=request.user)
        form_obj.delete()
        messages.success(request, 'فرم حذف شد.')
        return redirect('forms_builder:form_list')
