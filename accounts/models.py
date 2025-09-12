from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom user model with additional fields for mental health journal."""
    email = models.EmailField(unique=True)
    timezone = models.CharField(max_length=50, default='UTC')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Keep username field for Django Allauth compatibility but make it non-unique
    username = models.CharField(max_length=150, blank=True, null=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        # Set username to email for compatibility
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)


class UserSettings(models.Model):
    """User preferences and settings."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='settings')
    
    # Reminder settings
    reminder_time = models.TimeField(default='20:30')
    reminder_enabled = models.BooleanField(default=True)
    reminder_days = models.JSONField(default=list)  # List of weekdays [0-6]
    
    # Display preferences
    theme = models.CharField(max_length=10, choices=[('light', 'Light'), ('dark', 'Dark')], default='light')
    pin_enabled = models.BooleanField(default=False)
    pin_code = models.CharField(max_length=6, blank=True, null=True)
    
    # Privacy settings
    share_links_enabled = models.BooleanField(default=True)
    share_link_duration_days = models.IntegerField(default=7)
    
    # Pro features
    is_pro = models.BooleanField(default=False)
    pro_expires_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email} settings"


class EmotionTag(models.Model):
    """Predefined emotion tags that users can select."""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6c757d')  # Hex color
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class ActivityTag(models.Model):
    """Predefined activity tags that users can select."""
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6c757d')  # Hex color
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UserEmotionTag(models.Model):
    """User's selected emotion tags."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='emotion_tags')
    emotion = models.ForeignKey(EmotionTag, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'emotion']
        ordering = ['order', 'emotion__name']
    
    def __str__(self):
        return f"{self.user.email} - {self.emotion.name}"


class UserActivityTag(models.Model):
    """User's selected activity tags."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_tags')
    activity = models.ForeignKey(ActivityTag, on_delete=models.CASCADE)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'activity']
        ordering = ['order', 'activity__name']
    
    def __str__(self):
        return f"{self.user.email} - {self.activity.name}"
