import re

import jdatetime


PERSIAN_MONTHS = {
    1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد', 4: 'تیر',
    5: 'مرداد', 6: 'شهریور', 7: 'مهر', 8: 'آبان',
    9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند',
}


def to_gregorian(date_str: str):
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip().replace('-', '/')

    match = re.match(r'^(\d{4})/(\d{1,2})/(\d{1,2})$', date_str)
    if not match:
        return None

    y, m, d = int(match.group(1)), int(match.group(2)), int(match.group(3))

    if 1300 <= y <= 1500:
        try:
            return jdatetime.date(y, m, d).togregorian()
        except Exception:
            return None
    try:
        from datetime import date
        return date(y, m, d)
    except Exception:
        return None


def to_jalali(date_obj, short=False):
    """تبدیل تاریخ میلادی به شمسی"""
    if not date_obj:
        return '-'
    try:
        if hasattr(date_obj, 'date'):
            date_obj = date_obj.date()
        jd = jdatetime.date.fromgregorian(date=date_obj)
        if short:
            month_name = PERSIAN_MONTHS.get(jd.month, '')
            return f'{jd.day} {month_name}'
        return f'{jd.year}/{jd.month:02d}/{jd.day:02d}'
    except Exception:
        return str(date_obj)
