from django.contrib import admin
from .models import Insight, Correlation


@admin.register(Insight)
class InsightAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'insight_type', 'is_active', 'is_read', 'created_at')
    list_filter = ('insight_type', 'is_active', 'is_read', 'created_at')
    search_fields = ('user__email', 'title', 'description')
    date_hierarchy = 'created_at'


@admin.register(Correlation)
class CorrelationAdmin(admin.ModelAdmin):
    list_display = ('user', 'metric1', 'metric2', 'correlation_coefficient', 'sample_size', 'created_at')
    list_filter = ('metric1', 'metric2', 'created_at')
    search_fields = ('user__email',)
    date_hierarchy = 'created_at'
