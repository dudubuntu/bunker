from django.contrib import admin

from .models import *


admin.site.register(Player)
admin.site.register(Room)
admin.site.register(RoomUser)
admin.site.register(RoomVote)