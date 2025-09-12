from django.urls import path
from . import views

app_name = 'insights'

urlpatterns = [
    path('', views.InsightsView.as_view(), name='insights'),
    path('api/correlations/', views.CorrelationsAPIView.as_view(), name='correlations_api'),
    path('api/generate/', views.GenerateInsightsView.as_view(), name='generate_insights'),
]
