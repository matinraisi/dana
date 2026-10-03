# apps/accounting/utils.py
from arabic_reshaper import reshape
from bidi.algorithm import get_display

def fa_convert(text):
    if not text:
        return ""
    return get_display(reshape(str(text)))