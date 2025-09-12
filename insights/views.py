from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, View
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from .models import Insight, Correlation
from journal.models import JournalEntry, EntryEmotion, EntryActivity


class InsightsView(LoginRequiredMixin, TemplateView):
    """Main insights dashboard."""
    template_name = 'insights/insights.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get time range
        days = int(self.request.GET.get('days', 30))
        start_date = timezone.now().date() - timedelta(days=days)
        
        # Get user's insights
        try:
            context['insights'] = user.insights.filter(
                start_date__lte=start_date,
                end_date__gte=timezone.now().date(),
                is_active=True
            ).order_by('-created_at')[:10]
        except:
            context['insights'] = []
        
        # Get correlations
        try:
            context['correlations'] = user.correlations.filter(
                start_date__lte=start_date,
                end_date__gte=timezone.now().date()
            ).order_by('-correlation_coefficient')[:5]
        except:
            context['correlations'] = []
        
        context['days'] = days
        return context


class CorrelationsAPIView(LoginRequiredMixin, View):
    """API endpoint for correlation data."""
    
    def get(self, request):
        """Get correlation data for charts."""
        user = request.user
        days = int(request.GET.get('days', 30))
        
        # Get entries for the specified number of days
        start_date = timezone.now().date() - timedelta(days=days)
        entries = user.entries.filter(date__gte=start_date).order_by('date')
        
        if entries.count() < 2:  # Need at least 2 data points
            return JsonResponse({'message': 'Not enough data for correlations'})
        
        # Prepare data for correlation analysis
        data = []
        for entry in entries:
            # Count emotions and activities
            emotion_count = entry.emotions.count()
            activity_count = entry.activities.count()
            
            data.append({
                'date': entry.date.isoformat(),
                'mood_rating': entry.mood_rating,
                'stress_level': entry.stress_level or 0,
                'sleep_hours': entry.sleep_hours or 0,
                'emotion_count': emotion_count,
                'activity_count': activity_count,
            })
        
        # Convert to DataFrame for correlation analysis
        df = pd.DataFrame(data)
        
        # Calculate correlations
        correlations = {}
        metrics = ['mood_rating', 'stress_level', 'sleep_hours', 'emotion_count', 'activity_count']
        
        for metric1 in metrics:
            for metric2 in metrics:
                if metric1 != metric2 and df[metric1].notna().sum() > 0 and df[metric2].notna().sum() > 0:
                    corr = df[metric1].corr(df[metric2])
                    if not np.isnan(corr):
                        correlations[f"{metric1}_vs_{metric2}"] = {
                            'correlation': round(corr, 3),
                            'sample_size': len(df)
                        }
        
        return JsonResponse({
            'data': data,
            'correlations': correlations,
            'summary': {
                'total_entries': len(data),
                'date_range': f"{start_date} to {timezone.now().date()}",
            }
        })


class GenerateInsightsView(LoginRequiredMixin, View):
    """Generate new insights for the user."""
    
    def post(self, request):
        """Generate insights based on user data."""
        try:
            user = request.user
            days = int(request.POST.get('days', 30))
            print(f"Generating insights for user {user.email}, {days} days")
            
            # Get entries for analysis
            start_date = timezone.now().date() - timedelta(days=days)
            entries = user.entries.filter(date__gte=start_date).order_by('date')
            print(f"Found {entries.count()} entries")
            
            if entries.count() < 1:
                print("Not enough data for insights")
                return JsonResponse({'success': False, 'message': 'Not enough data for insights'})
            
            # Generate insights
            print("Starting insight generation...")
            insights = self.generate_insights(user, entries, start_date, timezone.now().date())
            print(f"Generated {len(insights)} insights")
            
            return JsonResponse({'success': True, 'insights': insights})
            
        except Exception as e:
            import traceback
            print(f"Error in GenerateInsightsView: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    def generate_insights(self, user, entries, start_date, end_date):
        """Generate insights based on entry data."""
        insights = []
        print("Starting generate_insights method")
        
        # Calculate basic statistics
        mood_ratings = [e.mood_rating for e in entries if e.mood_rating is not None]
        stress_levels = [e.stress_level for e in entries if e.stress_level is not None]
        sleep_hours = [e.sleep_hours for e in entries if e.sleep_hours is not None]
        
        print(f"Mood ratings: {len(mood_ratings)}")
        print(f"Stress levels: {len(stress_levels)}")
        print(f"Sleep hours: {len(sleep_hours)}")
        
        # Basic mood insights (works with any number of entries)
        if mood_ratings:
            avg_mood = sum(mood_ratings) / len(mood_ratings)
            min_mood = min(mood_ratings)
            max_mood = max(mood_ratings)
            
            # Mood summary insight
            mood_description = f"Your average mood over {len(entries)} entries is {avg_mood:.1f}/10"
            if len(mood_ratings) > 1:
                mood_range = max_mood - min_mood
                if mood_range > 3:
                    mood_description += f". You've experienced a wide range of moods ({min_mood}-{max_mood}), which is normal for mental health tracking."
                else:
                    mood_description += f". Your mood has been relatively stable ({min_mood}-{max_mood})."
            
            insights.append({
                'title': 'Mood Summary',
                'description': mood_description,
                'type': 'summary',
                'data': {'avg_mood': round(avg_mood, 2), 'min_mood': min_mood, 'max_mood': max_mood, 'entries': len(entries)}
            })
            
            # Mood trend insight (only if we have enough data)
            if len(mood_ratings) >= 3:
                mood_trend = self.calculate_trend(mood_ratings)
                if mood_trend > 0.1:
                    insights.append({
                        'title': 'Positive Mood Trend',
                        'description': f'Your mood has been improving over the last {len(entries)} days!',
                        'type': 'trend',
                        'data': {'trend': mood_trend, 'avg_mood': round(avg_mood, 2)}
                    })
                elif mood_trend < -0.1:
                    insights.append({
                        'title': 'Mood Decline Detected',
                        'description': f'Your mood has been declining over the last {len(entries)} days. Consider reaching out for support.',
                        'type': 'trend',
                        'data': {'trend': mood_trend, 'avg_mood': round(avg_mood, 2)}
                    })
        
        # Sleep insights
        if sleep_hours:
            avg_sleep = sum(sleep_hours) / len(sleep_hours)
            sleep_description = f"Your average sleep is {avg_sleep:.1f} hours per night"
            if avg_sleep < 7:
                sleep_description += ". Consider aiming for 7-9 hours for better mental health."
            elif avg_sleep > 9:
                sleep_description += ". You're getting plenty of sleep!"
            else:
                sleep_description += ". This is a healthy amount of sleep."
            
            insights.append({
                'title': 'Sleep Analysis',
                'description': sleep_description,
                'type': 'summary',
                'data': {'avg_sleep': round(avg_sleep, 2), 'entries': len(sleep_hours)}
            })
        
        # Stress insights
        if stress_levels:
            avg_stress = sum(stress_levels) / len(stress_levels)
            stress_description = f"Your average stress level is {avg_stress:.1f}/10"
            if avg_stress > 7:
                stress_description += ". Consider stress management techniques like deep breathing or meditation."
            elif avg_stress < 4:
                stress_description += ". You're managing stress well!"
            else:
                stress_description += ". This is a moderate stress level."
            
            insights.append({
                'title': 'Stress Analysis',
                'description': stress_description,
                'type': 'summary',
                'data': {'avg_stress': round(avg_stress, 2), 'entries': len(stress_levels)}
            })
        
        # Correlations (only if we have enough data)
        if len(entries) >= 3:
            # Sleep and mood correlation
            if sleep_hours and mood_ratings and len(sleep_hours) >= 2:
                sleep_mood_corr = self.calculate_correlation(sleep_hours, mood_ratings)
                if abs(sleep_mood_corr) > 0.2:  # Lower threshold for fewer data points
                    insights.append({
                        'title': 'Sleep-Mood Connection',
                        'description': f'There\'s a {"positive" if sleep_mood_corr > 0 else "negative"} correlation between your sleep and mood.',
                        'type': 'correlation',
                        'data': {'correlation': round(sleep_mood_corr, 3)}
                    })
            
            # Stress and mood correlation
            if stress_levels and mood_ratings and len(stress_levels) >= 2:
                stress_mood_corr = self.calculate_correlation(stress_levels, mood_ratings)
                if abs(stress_mood_corr) > 0.2:  # Lower threshold for fewer data points
                    insights.append({
                        'title': 'Stress-Mood Connection',
                        'description': f'There\'s a {"negative" if stress_mood_corr < 0 else "positive"} correlation between your stress and mood.',
                        'type': 'correlation',
                        'data': {'correlation': round(stress_mood_corr, 3)}
                    })
        
        # Activity insights
        activity_insights = self.generate_activity_insights(entries)
        insights.extend(activity_insights)
        
        # Save insights to database
        print(f"Saving {len(insights)} insights to database")
        for insight_data in insights:
            try:
                Insight.objects.create(
                    user=user,
                    title=insight_data['title'],
                    description=insight_data['description'],
                    insight_type=insight_data['type'],
                    data=insight_data['data'],
                    start_date=start_date,
                    end_date=end_date
                )
                print(f"Created insight: {insight_data['title']}")
            except Exception as e:
                print(f"Error creating insight {insight_data['title']}: {str(e)}")
                raise e
        
        print("All insights saved successfully")
        return insights
    
    def generate_activity_insights(self, entries):
        """Generate insights about activities and emotions."""
        insights = []
        
        # Count activities and emotions across all entries
        activity_counts = {}
        emotion_counts = {}
        
        for entry in entries:
            # Count activities
            for activity in entry.activities.all():
                activity_name = activity.activity.name
                activity_counts[activity_name] = activity_counts.get(activity_name, 0) + 1
            
            # Count emotions
            for emotion in entry.emotions.all():
                emotion_name = emotion.emotion.name
                emotion_counts[emotion_name] = emotion_counts.get(emotion_name, 0) + 1
        
        # Activity insights
        if activity_counts:
            most_common_activity = max(activity_counts, key=activity_counts.get)
            total_activities = sum(activity_counts.values())
            
            insights.append({
                'title': 'Most Common Activity',
                'description': f'You\'ve logged "{most_common_activity}" {activity_counts[most_common_activity]} times. This seems to be an important part of your routine.',
                'type': 'pattern',
                'data': {'activity': most_common_activity, 'count': activity_counts[most_common_activity], 'total': total_activities}
            })
        
        # Emotion insights
        if emotion_counts:
            most_common_emotion = max(emotion_counts, key=emotion_counts.get)
            total_emotions = sum(emotion_counts.values())
            
            insights.append({
                'title': 'Most Common Emotion',
                'description': f'You\'ve logged "{most_common_emotion}" {emotion_counts[most_common_emotion]} times. This gives insight into your emotional patterns.',
                'type': 'pattern',
                'data': {'emotion': most_common_emotion, 'count': emotion_counts[most_common_emotion], 'total': total_emotions}
            })
        
        return insights
    
    def calculate_trend(self, values):
        """Calculate trend using linear regression."""
        if len(values) < 2:
            return 0
        
        x = list(range(len(values)))
        n = len(values)
        
        # Simple linear regression
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        return slope
    
    def calculate_correlation(self, x, y):
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        sum_y2 = sum(y[i] ** 2 for i in range(n))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x2 - sum_x ** 2) * (n * sum_y2 - sum_y ** 2)) ** 0.5
        
        if denominator == 0:
            return 0
        
        return numerator / denominator
