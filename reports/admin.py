from django.contrib import admin
from .models import Report, ReportAccess


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'report_type', 'start_date', 'end_date', 'is_public', 'created_at')
    list_filter = ('report_type', 'is_public', 'created_at')
    search_fields = ('user__email', 'title')
    date_hierarchy = 'created_at'
    readonly_fields = ('share_token', 'created_at', 'updated_at')


@admin.register(ReportAccess)
class ReportAccessAdmin(admin.ModelAdmin):
    list_display = ('report', 'ip_address', 'accessed_at')
    list_filter = ('accessed_at',)
    search_fields = ('report__title', 'ip_address')
    date_hierarchy = 'accessed_at'
