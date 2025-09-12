from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import EmotionTag, ActivityTag

User = get_user_model()


class JournalEntry(models.Model):
    """Daily journal entry for mood tracking."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='entries')
    date = models.DateField(default=timezone.now)
    
    # Core mood data
    mood_rating = models.IntegerField(choices=[(i, i) for i in range(11)], help_text="Mood rating from 0-10")
    
    # Optional metrics
    stress_level = models.IntegerField(choices=[(i, i) for i in range(11)], null=True, blank=True, help_text="Stress level from 0-10")
    sleep_hours = models.FloatField(null=True, blank=True, help_text="Hours of sleep")
    
    # Free text
    notes = models.TextField(blank=True, help_text="Free text notes about the day")
    quick_prompt = models.TextField(blank=True, help_text="Response to daily prompt")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date', '-created_at']
        verbose_name_plural = 'Journal Entries'
    
    def __str__(self):
        return f"{self.user.email} - {self.date} (Mood: {self.mood_rating})"
    
    @classmethod
    def get_daily_average_mood(cls, user, date):
        """Calculate average mood for a specific day."""
        entries = cls.objects.filter(user=user, date=date)
        if not entries.exists():
            return None
        return entries.aggregate(avg_mood=models.Avg('mood_rating'))['avg_mood']
    
    @classmethod
    def get_daily_average_stress(cls, user, date):
        """Calculate average stress level for a specific day."""
        entries = cls.objects.filter(user=user, date=date, stress_level__isnull=False)
        if not entries.exists():
            return None
        return entries.aggregate(avg_stress=models.Avg('stress_level'))['avg_stress']
    
    @classmethod
    def get_daily_average_sleep(cls, user, date):
        """Calculate average sleep hours for a specific day."""
        entries = cls.objects.filter(user=user, date=date, sleep_hours__isnull=False)
        if not entries.exists():
            return None
        return entries.aggregate(avg_sleep=models.Avg('sleep_hours'))['avg_sleep']


class EntryEmotion(models.Model):
    """Many-to-many relationship between entries and emotions."""
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='emotions')
    emotion = models.ForeignKey(EmotionTag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['entry', 'emotion']
    
    def __str__(self):
        return f"{self.entry.date} - {self.emotion.name}"


class EntryActivity(models.Model):
    """Many-to-many relationship between entries and activities."""
    entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name='activities')
    activity = models.ForeignKey(ActivityTag, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['entry', 'activity']
    
    def __str__(self):
        return f"{self.entry.date} - {self.activity.name}"


class DailyPrompt(models.Model):
    """Rotating daily prompts for journal entries."""
    text = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', 'created_at']
    
    def __str__(self):
        return self.text


class ReminderLog(models.Model):
    """Log of sent reminders for tracking and analytics."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reminder_logs')
    sent_at = models.DateTimeField(auto_now_add=True)
    reminder_type = models.CharField(max_length=20, choices=[
        ('daily', 'Daily Reminder'),
        ('missed', 'Missed Days'),
        ('weekly', 'Weekly Summary'),
    ])
    email_sent = models.BooleanField(default=True)
    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-sent_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.reminder_type} - {self.sent_at.date()}"
