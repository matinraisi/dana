# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, 'D:\\project\\AAA\\cademy')
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()
from apps.schools.models import School
s = School.objects.get(id=1)
print('Old title was:', repr(s.title))
s.title = 'آکادمی هوش مصنوعی سانتک'
s.save()
print('New title is:', repr(s.title))
