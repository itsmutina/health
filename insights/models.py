from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Insight(models.Model):
    """Generated insights and correlations for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='insights')
    
    # Insight metadata
    title = models.CharField(max_length=200)
    description = models.TextField()
    insight_type = models.CharField(max_length=50, choices=[
        ('correlation', 'Correlation'),
        ('pattern', 'Pattern'),
        ('trend', 'Trend'),
        ('recommendation', 'Recommendation'),
    ])
    
    # Data for the insight
    data = models.JSONField(default=dict)  # Store charts data, correlations, etc.
    
    # Time range this insight covers
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Insight status
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"


class Correlation(models.Model):
    """Stored correlation calculations between different metrics."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='correlations')
    
    # What we're correlating
    metric1 = models.CharField(max_length=50)  # e.g., 'mood_rating', 'sleep_hours'
    metric2 = models.CharField(max_length=50)  # e.g., 'stress_level', 'exercise'
    
    # Correlation data
    correlation_coefficient = models.FloatField()
    p_value = models.FloatField(null=True, blank=True)
    sample_size = models.IntegerField()
    
    # Time range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'metric1', 'metric2', 'start_date', 'end_date']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.metric1} vs {self.metric2}: {self.correlation_coefficient:.3f}"
