from django import forms
from allauth.account.forms import SignupForm, LoginForm
from .models import User


class CustomSignupForm(SignupForm):
    """Custom signup form for our User model."""
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    
    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()
        return user


class CustomLoginForm(LoginForm):
    """Custom login form for our User model."""
    pass
