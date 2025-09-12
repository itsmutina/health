from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportsView.as_view(), name='reports'),
    path('generate/', views.GenerateReportView.as_view(), name='generate_report'),
    path('share/<uuid:token>/', views.SharedReportView.as_view(), name='shared_report'),
    path('download/<int:report_id>/', views.DownloadReportView.as_view(), name='download_report'),
    path('share/<uuid:token>/download/', views.DownloadSharedReportView.as_view(), name='download_shared_report'),
]
