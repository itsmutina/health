from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import JsonResponse, HttpResponse
from django.core import serializers
from django.utils import timezone
import json
import csv
from .models import UserSettings, EmotionTag, ActivityTag, UserEmotionTag, UserActivityTag


class ProfileView(LoginRequiredMixin, TemplateView):
    """User profile view."""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = self.request.user.settings
        return context


class SettingsView(LoginRequiredMixin, TemplateView):
    """User settings view."""
    template_name = 'accounts/settings.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['settings'] = user.settings
        context['emotion_tags'] = EmotionTag.objects.filter(is_default=True)
        context['activity_tags'] = ActivityTag.objects.filter(is_default=True)
        context['user_emotion_tags'] = user.emotion_tags.all()
        context['user_activity_tags'] = user.activity_tags.all()
        return context


class UpdateSettingsView(LoginRequiredMixin, View):
    """Update user settings via AJAX."""
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            settings = request.user.settings
            
            # Update reminder settings
            if 'reminder_time' in data:
                from datetime import datetime
                time_str = data['reminder_time']
                settings.reminder_time = datetime.strptime(time_str, '%H:%M').time()
            if 'reminder_enabled' in data:
                settings.reminder_enabled = data['reminder_enabled']
            if 'reminder_days' in data:
                settings.reminder_days = data['reminder_days']
            
            # Update display preferences
            if 'theme' in data:
                settings.theme = data['theme']
            if 'pin_enabled' in data:
                settings.pin_enabled = data['pin_enabled']
            if 'pin_code' in data:
                settings.pin_code = data['pin_code']
            
            # Update privacy settings
            if 'share_links_enabled' in data:
                settings.share_links_enabled = data['share_links_enabled']
            if 'share_link_duration_days' in data:
                settings.share_link_duration_days = data['share_link_duration_days']
            
            # Update emotion tags
            if 'emotions' in data:
                from .models import UserEmotionTag
                # Clear existing emotion tags
                UserEmotionTag.objects.filter(user=request.user).delete()
                # Add new emotion tags
                for emotion_id in data['emotions']:
                    try:
                        emotion = EmotionTag.objects.get(id=emotion_id)
                        UserEmotionTag.objects.create(user=request.user, emotion=emotion)
                    except EmotionTag.DoesNotExist:
                        pass
            
            # Update activity tags
            if 'activities' in data:
                from .models import UserActivityTag
                # Clear existing activity tags
                UserActivityTag.objects.filter(user=request.user).delete()
                # Add new activity tags
                for activity_id in data['activities']:
                    try:
                        activity = ActivityTag.objects.get(id=activity_id)
                        UserActivityTag.objects.create(user=request.user, activity=activity)
                    except ActivityTag.DoesNotExist:
                        pass
            
            settings.save()
            
            return JsonResponse({'success': True, 'message': 'Settings updated successfully'})
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})


class DeleteAccountView(LoginRequiredMixin, View):
    """Delete user account and all associated data."""
    
    def post(self, request):
        try:
            user = request.user
            user.delete()  # This will cascade delete all related data
            messages.success(request, 'Your account has been deleted successfully.')
            return redirect('account_login')
        except Exception as e:
            messages.error(request, f'Error deleting account: {str(e)}')
            return redirect('accounts:settings')


class ExportDataView(LoginRequiredMixin, View):
    """Export user data in CSV format."""
    
    def get(self, request):
        user = request.user
        format_type = request.GET.get('format', 'csv')
        
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="{user.email}_data.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Data Type', 'Date', 'Mood', 'Stress', 'Sleep Hours', 'Notes', 'Emotions', 'Activities'])
            
            # Export journal entries
            for entry in user.entries.all():
                emotions = ', '.join([e.emotion.name for e in entry.emotions.all()])
                activities = ', '.join([a.activity.name for a in entry.activities.all()])
                writer.writerow([
                    'Journal Entry',
                    entry.date,
                    entry.mood_rating,
                    entry.stress_level,
                    entry.sleep_hours,
                    entry.notes,
                    emotions,
                    activities
                ])
            
            return response
        
        elif format_type == 'json':
            # Export as JSON
            data = {
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'timezone': user.timezone,
                    'created_at': user.created_at.isoformat(),
                },
                'settings': {
                    'reminder_time': user.settings.reminder_time.isoformat(),
                    'reminder_enabled': user.settings.reminder_enabled,
                    'theme': user.settings.theme,
                },
                'entries': []
            }
            
            for entry in user.entries.all():
                data['entries'].append({
                    'date': entry.date.isoformat(),
                    'mood_rating': entry.mood_rating,
                    'stress_level': entry.stress_level,
                    'sleep_hours': entry.sleep_hours,
                    'notes': entry.notes,
                    'emotions': [e.emotion.name for e in entry.emotions.all()],
                    'activities': [a.activity.name for a in entry.activities.all()],
                })
            
            response = HttpResponse(json.dumps(data, indent=2), content_type='application/json')
            response['Content-Disposition'] = f'attachment; filename="{user.email}_data.json"'
            return response
        
        return JsonResponse({'error': 'Invalid format'}, status=400)
