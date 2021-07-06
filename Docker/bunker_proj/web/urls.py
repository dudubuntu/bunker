from django.urls import path

from .views import *


app_name = 'web'
urlpatterns = [
    path('', index, name='index'),
    path('room/<int:id>', room, name='room'),
]