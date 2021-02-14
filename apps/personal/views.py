from django.shortcuts import render
from django.conf import settings


def home_screen_view(request, *args, **kwargs):
    context = {
        'debug_mode': settings.DEBUG,
        'room_id': 2,
    }
    return render(request, "personal/home.html", context)
