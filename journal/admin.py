from django.contrib import admin
from .models import JournalEntry, EntryEmotion, EntryActivity, DailyPrompt, ReminderLog


@admin.register(JournalEntry)
class JournalEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'mood_rating', 'stress_level', 'sleep_hours', 'created_at')
    list_filter = ('date', 'mood_rating', 'created_at')
    search_fields = ('user__email', 'notes')
    date_hierarchy = 'date'
    readonly_fields = ('created_at', 'updated_at')


@admin.register(EntryEmotion)
class EntryEmotionAdmin(admin.ModelAdmin):
    list_display = ('entry', 'emotion', 'created_at')
    list_filter = ('emotion', 'created_at')
    search_fields = ('entry__user__email', 'emotion__name')


@admin.register(EntryActivity)
class EntryActivityAdmin(admin.ModelAdmin):
    list_display = ('entry', 'activity', 'created_at')
    list_filter = ('activity', 'created_at')
    search_fields = ('entry__user__email', 'activity__name')


@admin.register(DailyPrompt)
class DailyPromptAdmin(admin.ModelAdmin):
    list_display = ('text', 'is_active', 'order', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('text',)


@admin.register(ReminderLog)
class ReminderLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'reminder_type', 'sent_at', 'email_sent', 'clicked')
    list_filter = ('reminder_type', 'email_sent', 'clicked', 'sent_at')
    search_fields = ('user__email',)
    date_hierarchy = 'sent_at'
