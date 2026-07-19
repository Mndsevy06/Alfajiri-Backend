from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display  = ['titre', 'type', 'module', 'user', 'lu', 'cree_le']
    list_filter   = ['type', 'module', 'lu']
    search_fields = ['titre', 'message', 'user__email']
    readonly_fields = ['id', 'cree_le']
    ordering = ['-cree_le']
