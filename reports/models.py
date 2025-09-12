from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()


class Report(models.Model):
    """Generated reports for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports')
    
    # Report metadata
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=[
        ('weekly', 'Weekly Report'),
        ('monthly', 'Monthly Report'),
        ('custom', 'Custom Report'),
    ])
    
    # Date range
    start_date = models.DateField()
    end_date = models.DateField()
    
    # Report data (JSON)
    data = models.JSONField(default=dict)
    
    # File storage
    pdf_file = models.FileField(upload_to='reports/', null=True, blank=True)
    
    # Sharing
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    share_expires_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    @property
    def is_share_expired(self):
        """Check if share link has expired."""
        if not self.share_expires_at:
            return False
        return timezone.now() > self.share_expires_at


class ReportAccess(models.Model):
    """Track access to shared reports."""
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='access_logs')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"{self.report.title} - {self.accessed_at}"
