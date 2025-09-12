"""
URL configuration for mental_health_journal project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls')),
    path('insights/', include('insights.urls')),
    path('reports/', include('reports.urls')),
    path('', TemplateView.as_view(template_name='landing.html'), name='landing'),
    path('app/', include('journal.urls')),  # Main app URLs
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
