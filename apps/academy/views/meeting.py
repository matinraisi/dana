import hashlib
import string
import random
import urllib.parse
from django.shortcuts import render, redirect
from django.views import View
from django.conf import settings
from django.urls import reverse
from django.http import Http404
from django.contrib.auth.mixins import LoginRequiredMixin


def generate_room_id():
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    h = hashlib.md5(rand.encode()).hexdigest()[:8]
    return f"academy-{h}"


class MeetingHomeView(LoginRequiredMixin, View):
    def get(self, request):
        room_id = request.GET.get('room', '').strip()
        if room_id:
            return redirect('academy:meeting_room', room_id=room_id)
        return render(request, 'academy/dashboard/meeting_home.html', {
            'jitsi_domain': settings.JITSI_DOMAIN,
        })


class MeetingRoomView(LoginRequiredMixin, View):
    def get(self, request, room_id):
        if not room_id or len(room_id) < 3:
            raise Http404("نام اتاق نامعتبر است")
        return render(request, 'academy/dashboard/meeting_room.html', {
            'room_id': room_id,
            'jitsi_domain': settings.JITSI_DOMAIN,
        })


class MeetingCreateView(LoginRequiredMixin, View):
    def get(self, request):
        room_id = generate_room_id()
        return redirect('academy:meeting_room', room_id=room_id)


class MeetingExternalView(LoginRequiredMixin, View):
    def get(self, request):
        url = request.GET.get('url', '').strip()
        if not url:
            return redirect('academy:meeting_home')
        if not url.startswith(('http://', 'https://')):
            return redirect('academy:meeting_home')
        return render(request, 'academy/dashboard/meeting_external.html', {
            'meeting_url': url,
        })
