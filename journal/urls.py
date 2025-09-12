from django.urls import path
from . import views

app_name = 'journal'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('onboarding/', views.OnboardingView.as_view(), name='onboarding'),
    path('entry/new/', views.NewEntryView.as_view(), name='new_entry'),
    path('entry/<int:entry_id>/edit/', views.EditEntryView.as_view(), name='edit_entry'),
    path('entry/<int:entry_id>/delete/', views.DeleteEntryView.as_view(), name='delete_entry'),
    path('history/', views.HistoryView.as_view(), name='history'),
    path('api/entries/', views.EntriesAPIView.as_view(), name='entries_api'),
    path('api/stats/', views.StatsAPIView.as_view(), name='stats_api'),
    path('api/quick-add/', views.QuickAddAPIView.as_view(), name='quick_add_api'),
]
