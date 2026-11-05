from django.contrib import admin

from .models import StaffMember


@admin.register(StaffMember)
class StaffMemberAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "role", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("full_name", "email", "phone")
