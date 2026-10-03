from django import template

register = template.Library()


@register.filter
def toman(value):
    """Format number with comma separators."""
    try:
        num = int(value)
        return f'{num:,}'
    except (ValueError, TypeError):
        return value


@register.filter
def persian_number(value):
    """Format number with comma separators."""
    try:
        num = int(value)
        return f'{num:,}'
    except (ValueError, TypeError):
        return value


@register.filter
def jalali(value):
    """Convert Gregorian date to Jalali string."""
    if not value:
        return '-'
    try:
        from apps.academy.utils.date_helper import to_jalali
        return to_jalali(value)
    except Exception:
        return str(value)


@register.filter
def jalali_short(value):
    """Convert to short Jalali (day month)."""
    if not value:
        return '-'
    try:
        from apps.academy.utils.date_helper import to_jalali
        return to_jalali(value, short=True)
    except Exception:
        return str(value)
