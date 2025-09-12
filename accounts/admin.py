from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserSettings, EmotionTag, ActivityTag, UserEmotionTag, UserActivityTag


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom user admin with email as primary field."""
    list_display = ('email', 'first_name', 'last_name', 'is_verified', 'is_staff', 'created_at')
    list_filter = ('is_verified', 'is_staff', 'is_superuser', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'timezone')}),
        ('Permissions', {'fields': ('is_active', 'is_verified', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    readonly_fields = ('created_at',)
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'reminder_enabled', 'reminder_time', 'theme', 'is_pro')
    list_filter = ('reminder_enabled', 'theme', 'is_pro')
    search_fields = ('user__email',)


@admin.register(EmotionTag)
class EmotionTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name',)


@admin.register(ActivityTag)
class ActivityTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('name',)


@admin.register(UserEmotionTag)
class UserEmotionTagAdmin(admin.ModelAdmin):
    list_display = ('user', 'emotion', 'order')
    list_filter = ('emotion',)
    search_fields = ('user__email', 'emotion__name')


@admin.register(UserActivityTag)
class UserActivityTagAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity', 'order')
    list_filter = ('activity',)
    search_fields = ('user__email', 'activity__name')
