from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta
from .models import JournalEntry, EntryEmotion, EntryActivity, DailyPrompt
from accounts.models import EmotionTag, ActivityTag, UserEmotionTag, UserActivityTag


class HomeView(LoginRequiredMixin, TemplateView):
    """Main dashboard view."""
    template_name = 'journal/home.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user has completed onboarding
        if not hasattr(request.user, 'settings'):
            from accounts.models import UserSettings
            UserSettings.objects.create(user=request.user)
            from django.shortcuts import redirect
            return redirect('journal:onboarding')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get unique dates with entries for the last 30 days
        from datetime import timedelta
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        entries = user.entries.filter(date__gte=thirty_days_ago)
        
        # Get unique dates and calculate daily averages
        unique_dates = entries.values_list('date', flat=True).distinct().order_by('-date')
        daily_data = []
        
        for date in unique_dates[:7]:  # Last 7 days
            daily_entries = entries.filter(date=date)
            avg_mood = JournalEntry.get_daily_average_mood(user, date)
            avg_stress = JournalEntry.get_daily_average_stress(user, date)
            avg_sleep = JournalEntry.get_daily_average_sleep(user, date)
            
            daily_data.append({
                'date': date,
                'avg_mood': round(avg_mood, 1) if avg_mood else None,
                'avg_stress': round(avg_stress, 1) if avg_stress else None,
                'avg_sleep': round(avg_sleep, 1) if avg_sleep else None,
                'entry_count': daily_entries.count(),
                'entries': daily_entries
            })
        
        context['daily_data'] = daily_data
        context['recent_entries'] = daily_data  # For backward compatibility
        context['total_entries'] = entries.count()
        
        # Calculate 7-day average mood
        if daily_data:
            mood_values = [d['avg_mood'] for d in daily_data if d['avg_mood'] is not None]
            context['avg_mood_7d'] = round(sum(mood_values) / len(mood_values), 1) if mood_values else None
            context['streak'] = self.calculate_streak(user)
        else:
            context['avg_mood_7d'] = None
            context['streak'] = 0
        
        # Get today's entries (all entries for today)
        today = timezone.now().date()
        context['today'] = today
        context['today_entries'] = user.entries.filter(date=today).order_by('-created_at')
        context['today_entry'] = context['today_entries'].first()  # For backward compatibility
        
        # Get daily prompt
        context['daily_prompt'] = DailyPrompt.objects.filter(is_active=True).order_by('?').first()
        
        return context
    
    def calculate_streak(self, user):
        """Calculate current logging streak."""
        entries = user.entries.all().order_by('-date')
        if not entries.exists():
            return 0
        
        streak = 0
        current_date = timezone.now().date()
        
        for entry in entries:
            if entry.date == current_date - timedelta(days=streak):
                streak += 1
                current_date = entry.date
            else:
                break
        
        return streak


class OnboardingView(LoginRequiredMixin, TemplateView):
    """3-step onboarding process."""
    template_name = 'journal/onboarding.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['emotion_tags'] = EmotionTag.objects.filter(is_default=True)
        context['activity_tags'] = ActivityTag.objects.filter(is_default=True)
        return context


class NewEntryView(LoginRequiredMixin, TemplateView):
    """Create new journal entry."""
    template_name = 'journal/new_entry.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        today = timezone.now().date()
        
        # Get user's selected tags
        context['user_emotion_tags'] = user.emotion_tags.all()
        context['user_activity_tags'] = user.activity_tags.all()
        
        # Get default activity tags as fallback
        context['activity_tags'] = ActivityTag.objects.filter(is_default=True)
        
        # Get daily prompt
        context['daily_prompt'] = DailyPrompt.objects.filter(is_active=True).order_by('?').first()
        
        # Get today's entries (if any)
        today_entries = JournalEntry.objects.filter(user=user, date=today).order_by('-created_at')
        context['today_entries'] = today_entries
        context['today_entry_count'] = today_entries.count()
        
        # For backward compatibility, set existing_entry to the most recent one
        context['existing_entry'] = today_entries.first() if today_entries.exists() else None
        if context['existing_entry']:
            context['existing_emotions'] = [e.emotion for e in context['existing_entry'].emotions.all()]
            context['existing_activities'] = [a.activity for a in context['existing_entry'].activities.all()]
        else:
            context['existing_emotions'] = []
            context['existing_activities'] = []
        
        return context


class EditEntryView(LoginRequiredMixin, View):
    """Edit existing journal entry."""
    
    def get(self, request, entry_id):
        entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
        user = request.user
        
        context = {
            'entry': entry,
            'user_emotion_tags': user.emotion_tags.all(),
            'user_activity_tags': user.activity_tags.all(),
            'selected_emotions': [e.emotion for e in entry.emotions.all()],
            'selected_activities': [a.activity for a in entry.activities.all()],
        }
        return render(request, 'journal/edit_entry.html', context)
    
    def post(self, request, entry_id):
        """Update existing journal entry."""
        try:
            data = json.loads(request.body)
            entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
            
            # Update entry fields
            entry.mood_rating = data['mood_rating']
            entry.stress_level = data.get('stress_level')
            entry.sleep_hours = data.get('sleep_hours')
            entry.notes = data.get('notes', '')
            entry.save()
            
            # Clear existing emotions and activities
            entry.emotions.all().delete()
            entry.activities.all().delete()
            
            # Add emotions
            for emotion_id in data.get('emotions', []):
                emotion = EmotionTag.objects.get(id=emotion_id)
                EntryEmotion.objects.create(entry=entry, emotion=emotion)
            
            # Add activities
            for activity_id in data.get('activities', []):
                activity = ActivityTag.objects.get(id=activity_id)
                EntryActivity.objects.create(entry=entry, activity=activity)
            
            return JsonResponse({
                'success': True, 
                'entry_id': entry.id,
                'action': 'updated',
                'message': 'Entry updated successfully!'
            })
            
        except Exception as e:
            import traceback
            print(f"Error in EditEntryView: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': str(e)})


class DeleteEntryView(LoginRequiredMixin, View):
    """Delete journal entry."""
    
    def post(self, request, entry_id):
        entry = get_object_or_404(JournalEntry, id=entry_id, user=request.user)
        entry.delete()
        messages.success(request, 'Entry deleted successfully.')
        return redirect('journal:home')


class HistoryView(LoginRequiredMixin, TemplateView):
    """View and search journal entries history."""
    template_name = 'journal/history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get filter parameters
        search = self.request.GET.get('search', '')
        mood_min = self.request.GET.get('mood_min', '')
        date_from = self.request.GET.get('date_from', '')
        date_to = self.request.GET.get('date_to', '')
        
        # Filter entries
        entries = user.entries.all()
        
        if search:
            entries = entries.filter(notes__icontains=search)
        
        if mood_min:
            entries = entries.filter(mood_rating__gte=int(mood_min))
        
        if date_from:
            entries = entries.filter(date__gte=datetime.strptime(date_from, '%Y-%m-%d').date())
        
        if date_to:
            entries = entries.filter(date__lte=datetime.strptime(date_to, '%Y-%m-%d').date())
        
        # Paginate results
        paginator = Paginator(entries, 20)
        page_number = self.request.GET.get('page')
        context['entries'] = paginator.get_page(page_number)
        
        # Pass filter values back to template
        context['search'] = search
        context['mood_min'] = mood_min
        context['date_from'] = date_from
        context['date_to'] = date_to
        
        return context


class EntriesAPIView(LoginRequiredMixin, View):
    """API endpoint for journal entries."""
    
    def get(self, request):
        """Get entries for charts and data."""
        user = request.user
        days = int(request.GET.get('days', 30))
        
        # Get entries for the specified number of days
        start_date = timezone.now().date() - timedelta(days=days)
        entries = user.entries.filter(date__gte=start_date).order_by('date')
        
        data = []
        for entry in entries:
            data.append({
                'date': entry.date.isoformat(),
                'mood_rating': entry.mood_rating,
                'stress_level': entry.stress_level,
                'sleep_hours': entry.sleep_hours,
                'notes': entry.notes,
                'emotions': [e.emotion.name for e in entry.emotions.all()],
                'activities': [a.activity.name for a in entry.activities.all()],
            })
        
        return JsonResponse({'entries': data})


class StatsAPIView(LoginRequiredMixin, View):
    """API endpoint for statistics and insights."""
    
    def get(self, request):
        """Get user statistics."""
        user = request.user
        days = int(request.GET.get('days', 30))
        
        # Get entries for the specified number of days
        start_date = timezone.now().date() - timedelta(days=days)
        entries = user.entries.filter(date__gte=start_date)
        
        if not entries.exists():
            return JsonResponse({'message': 'No data available'})
        
        # Calculate statistics
        avg_mood = entries.aggregate(avg=Avg('mood_rating'))['avg']
        avg_stress = entries.aggregate(avg=Avg('stress_level'))['avg']
        avg_sleep = entries.aggregate(avg=Avg('sleep_hours'))['avg']
        
        # Get most common emotions and activities
        emotion_counts = {}
        activity_counts = {}
        
        for entry in entries:
            for emotion in entry.emotions.all():
                emotion_counts[emotion.emotion.name] = emotion_counts.get(emotion.emotion.name, 0) + 1
            
            for activity in entry.activities.all():
                activity_counts[activity.activity.name] = activity_counts.get(activity.activity.name, 0) + 1
        
        # Sort by count
        top_emotions = sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        top_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return JsonResponse({
            'avg_mood': round(avg_mood, 2) if avg_mood else None,
            'avg_stress': round(avg_stress, 2) if avg_stress else None,
            'avg_sleep': round(avg_sleep, 2) if avg_sleep else None,
            'total_entries': entries.count(),
            'top_emotions': top_emotions,
            'top_activities': top_activities,
        })


class QuickAddAPIView(LoginRequiredMixin, View):
    """API endpoint for quick adding entries."""
    
    def post(self, request):
        """Create a new entry quickly."""
        try:
            data = json.loads(request.body)
            user = request.user
            today = timezone.now().date()
            
            # Create new entry (allow multiple entries per day)
            entry = JournalEntry.objects.create(
                user=user,
                date=today,
                mood_rating=data['mood_rating'],
                stress_level=data.get('stress_level'),
                sleep_hours=data.get('sleep_hours'),
                notes=data.get('notes', ''),
            )
            
            # Add emotions
            for emotion_id in data.get('emotions', []):
                emotion = EmotionTag.objects.get(id=emotion_id)
                EntryEmotion.objects.create(entry=entry, emotion=emotion)
            
            # Add activities
            for activity_id in data.get('activities', []):
                activity = ActivityTag.objects.get(id=activity_id)
                EntryActivity.objects.create(entry=entry, activity=activity)
            
            return JsonResponse({
                'success': True, 
                'entry_id': entry.id,
                'action': 'created',
                'message': 'Entry created successfully!'
            })
            
        except Exception as e:
            import traceback
            print(f"Error in QuickAddAPIView: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': str(e)})
