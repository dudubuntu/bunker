from django.contrib import admin

from .models import *


class RoomUserInLine(admin.TabularInline):
    model = RoomUser
    fields = ['username', 'player_number', 'game_sess_id']
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    
    inlines = [RoomUserInLine]
    list_filter = ['state']
    ordering = ['id']
    readonly_fields = ['created', 'updated']
    list_display = ['id', 'initiator', 'state', 'lap', 'turn', 'created']


admin.site.register(Player)
admin.site.register(RoomUser)
admin.site.register(RoomVote)