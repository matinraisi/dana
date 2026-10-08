import calendar
from datetime import date, timedelta, datetime, time
from django.shortcuts import render
from django.views import View
from apps.academy.mixins import AdminRequiredMixin

from ..models import Course, Session


PERSIAN_MONTHS = {
    1: 'فروردین', 2: 'اردیبهشت', 3: 'خرداد', 4: 'تیر',
    5: 'مرداد', 6: 'شهریور', 7: 'مهر', 8: 'آبان',
    9: 'آذر', 10: 'دی', 11: 'بهمن', 12: 'اسفند',
}


def gregorian_to_jalali(gy, gm, gd):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gm > 2:
        gy2 = gy + 1
    else:
        gy2 = gy
    days = 355666 + (365 * gy) + ((gy2 + 3) // 4) - ((gy2 + 99) // 100) + ((gy2 + 399) // 400) + gd + g_d_m[gm - 1]
    jy = -1595 + (33 * (days // 12053))
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + (days // 31)
        jd = 1 + (days % 31)
    else:
        jm = 7 + ((days - 186) // 30)
        jd = 1 + ((days - 186) % 30)
    return jy, jm, jd


def format_jalali(d):
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    month_name = PERSIAN_MONTHS.get(jm, '')
    return f'{jd} {month_name} {jy}'


def get_week_dates(target_date):
    weekday = target_date.weekday()
    saturday = target_date - timedelta(days=(weekday + 2) % 7)
    return [saturday + timedelta(days=i) for i in range(7)]


DAY_NAMES = ['دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنجشنبه', 'جمعه', 'شنبه', 'یکشنبه']


class TimetableView(AdminRequiredMixin, View):
    """جدول برنامه کلاس‌ها — مدل هفتگی"""

    def get(self, request):
        today = date.today()
        week_str = request.GET.get('week')
        if week_str:
            try:
                target_date = date.fromisoformat(week_str)
            except ValueError:
                target_date = today
        else:
            target_date = today

        week_dates = get_week_dates(target_date)
        week_start = week_dates[0]
        week_end = week_dates[6]

        sessions = (
            Session.objects.filter(date__gte=week_start, date__lte=week_end)
            .select_related('course', 'course__teacher', 'course__teacher__user')
            .order_by('date', 'start_time')
        )

        hours = list(range(7, 22))
        grid = {}
        for s in sessions:
            day_idx = (s.date.weekday() + 2) % 7
            hour = s.start_time.hour if s.start_time else 8
            if day_idx not in grid:
                grid[day_idx] = {}
            if hour not in grid[day_idx]:
                grid[day_idx][hour] = []
            grid[day_idx][hour].append(s)

        prev_week = week_start - timedelta(days=7)
        next_week = week_start + timedelta(days=7)
        week_start_jalali = format_jalali(week_start)
        week_end_jalali = format_jalali(week_end)

        context = {
            'week_dates': week_dates,
            'grid': grid,
            'hours': hours,
            'today': today,
            'prev_week': prev_week.isoformat(),
            'next_week': next_week.isoformat(),
            'week_start_jalali': week_start_jalali,
            'week_end_jalali': week_end_jalali,
            'sessions': sessions,
        }
        return render(request, 'academy/dashboard/timetable.html', context)


class RoomTimetableView(AdminRequiredMixin, View):
    """نمای فضا — کدوم کلاس کی پره/خالیه"""

    def get(self, request):
        today = date.today()
        week_str = request.GET.get('week')
        if week_str:
            try:
                target_date = date.fromisoformat(week_str)
            except ValueError:
                target_date = today
        else:
            target_date = today

        week_dates = get_week_dates(target_date)
        week_start = week_dates[0]
        week_end = week_dates[6]

        sessions = Session.objects.filter(date__gte=week_start, date__lte=week_end).select_related('course', 'course__teacher', 'course__teacher__user').order_by('date', 'start_time')

        # Get unique locations
        locations = sorted(set(s.location for s in sessions if s.location))

        # Build room grid: {location: {day_idx: {hour: [sessions]}}}
        hours = list(range(7, 22))
        room_grid = {}
        for loc in locations:
            room_grid[loc] = {}
            for s in sessions:
                if s.location == loc:
                    day_idx = (s.date.weekday() + 2) % 7
                    hour = s.start_time.hour if s.start_time else 8
                    if day_idx not in room_grid[loc]:
                        room_grid[loc][day_idx] = {}
                    if hour not in room_grid[loc][day_idx]:
                        room_grid[loc][day_idx][hour] = []
                    room_grid[loc][day_idx][hour].append(s)

        prev_week = week_start - timedelta(days=7)
        next_week = week_start + timedelta(days=7)

        context = {
            'week_dates': week_dates,
            'room_grid': room_grid,
            'locations': locations,
            'hours': hours,
            'today': today,
            'prev_week': prev_week.isoformat(),
            'next_week': next_week.isoformat(),
            'week_start_jalali': format_jalali(week_start),
            'week_end_jalali': format_jalali(week_end),
            'sessions': sessions,
        }
        return render(request, 'academy/dashboard/room_timetable.html', context)
