from django.urls import path

from .views import (
    AuthTokenRefreshView,
    BasicInformationView,
    FamilyCategoryView,
    FamilyMemberDetailView,
    FamilyMemberView,
    OTPRequestView,
    PhoneOTPLoginView,
    PhoneOTPRegisterView,
    UsernamePasswordLoginView,
    UsernamePasswordRegisterView,
)

urlpatterns = [
    path('register/', UsernamePasswordRegisterView.as_view(), name='register'),
    path('request-otp/', OTPRequestView.as_view(), name='request-otp'),
    path('register-phone/', PhoneOTPRegisterView.as_view(), name='register-phone'),
    path('login/password/', UsernamePasswordLoginView.as_view(), name='login-password'),
    path('login/otp/', PhoneOTPLoginView.as_view(), name='login-otp'),
    path('token/refresh/', AuthTokenRefreshView.as_view(), name='token-refresh'),
    path('basic-information/', BasicInformationView.as_view(), name='basic-information'),
    path('family-categories/', FamilyCategoryView.as_view(), name='family-categories'),
    path('family-members/', FamilyMemberView.as_view(), name='family-members'),
    path('family-members/<int:member_id>/', FamilyMemberDetailView.as_view(), name='family-member-detail'),
]
