from django.core.management.base import BaseCommand
from accounts.models import EmotionTag, ActivityTag
from journal.models import DailyPrompt


class Command(BaseCommand):
    help = 'Set up default emotion tags, activity tags, and daily prompts'

    def handle(self, *args, **options):
        self.stdout.write('Setting up default data...')
        
        # Create default emotion tags
        emotions = [
            ('Happy', '#f39c12'),
            ('Sad', '#3498db'),
            ('Anxious', '#e74c3c'),
            ('Calm', '#2ecc71'),
            ('Excited', '#9b59b6'),
            ('Frustrated', '#e67e22'),
            ('Grateful', '#1abc9c'),
            ('Lonely', '#34495e'),
            ('Hopeful', '#f1c40f'),
            ('Overwhelmed', '#e91e63'),
            ('Confident', '#27ae60'),
            ('Tired', '#95a5a6'),
        ]
        
        for name, color in emotions:
            emotion, created = EmotionTag.objects.get_or_create(
                name=name,
                defaults={'color': color, 'is_default': True}
            )
            if created:
                self.stdout.write(f'Created emotion tag: {name}')
        
        # Create default activity tags
        activities = [
            ('Exercise', '#e74c3c'),
            ('Work', '#3498db'),
            ('Socialized', '#2ecc71'),
            ('Read', '#9b59b6'),
            ('Meditation', '#1abc9c'),
            ('Cooking', '#f39c12'),
            ('Walking', '#27ae60'),
            ('Gaming', '#e67e22'),
            ('Music', '#8e44ad'),
            ('Sleep', '#34495e'),
            ('Cleaning', '#16a085'),
            ('Shopping', '#f1c40f'),
        ]
        
        for name, color in activities:
            activity, created = ActivityTag.objects.get_or_create(
                name=name,
                defaults={'color': color, 'is_default': True}
            )
            if created:
                self.stdout.write(f'Created activity tag: {name}')
        
        # Create daily prompts
        prompts = [
            "What was the highlight of your day?",
            "What's one thing you're grateful for today?",
            "What challenged you today and how did you handle it?",
            "What made you smile today?",
            "What would you like to do differently tomorrow?",
            "What's one thing you learned about yourself today?",
            "What helped you feel better today?",
            "What's something you're looking forward to?",
            "What's one small win you had today?",
            "How did you take care of yourself today?",
            "What's something you're proud of today?",
            "What's one thing that brought you peace today?",
        ]
        
        for i, prompt_text in enumerate(prompts):
            prompt, created = DailyPrompt.objects.get_or_create(
                text=prompt_text,
                defaults={'is_active': True, 'order': i}
            )
            if created:
                self.stdout.write(f'Created daily prompt: {prompt_text[:50]}...')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully set up default data!')
        )
