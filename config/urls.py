from django.contrib import admin
from django.urls import include, path

from .views import api_root, render_page

urlpatterns = [
    path('', render_page, name='frontend-dashboard'),
    path('dashboard/', render_page, {'page': 'dashboard'}, name='page-dashboard'),
    path('consultations/', render_page, {'page': 'consultations'}, name='page-consultations'),
    path('doctors/', render_page, {'page': 'doctors'}, name='page-doctors'),
    path('patients/', render_page, {'page': 'patients'}, name='page-patients'),
    path('analytics/', render_page, {'page': 'analytics'}, name='page-analytics'),
    path('settings/', render_page, {'page': 'settings'}, name='page-settings'),
    path('login/', render_page, {'page': 'login'}, name='page-login'),
    path('register/', render_page, {'page': 'register'}, name='page-register'),
    path('hc-auth/', render_page, {'page': 'hc-auth'}, name='page-hc-auth'),
    path('hc-profile/', render_page, {'page': 'hc-profile'}, name='page-hc-profile'),
    path('hc-family/', render_page, {'page': 'hc-family'}, name='page-hc-family'),
    path('hc-builder/', render_page, {'page': 'hc-builder'}, name='page-hc-builder'),
    path('hc-triage/', render_page, {'page': 'hc-triage'}, name='page-hc-triage'),
    path('hc-api/', render_page, {'page': 'hc-api'}, name='page-hc-api'),
    path('admin/', admin.site.urls),
    path('api/', api_root, name='api-root'),
    path('api/auth/', include('accounts.urls')),
    path('api/triage/', include('triage.urls')),
]
