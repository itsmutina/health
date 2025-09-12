from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('settings/', views.SettingsView.as_view(), name='settings'),
    path('settings/update/', views.UpdateSettingsView.as_view(), name='update_settings'),
    path('delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),
    path('export-data/', views.ExportDataView.as_view(), name='export_data'),
]
