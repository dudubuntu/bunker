from django.shortcuts import render
from django.shortcuts import get_object_or_404

from .models import Room


def index(request, *args, **kwargs):
    return render(request, template_name='web/index.html')


def room(request, id, *args, **kwargs):
    context = {
        'room': get_object_or_404(Room, id=id),
    }
    return render(request, template_name='web/room.html', context=context)