from django.urls import path
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .views import (
    AuthTokenRefreshView,
    BasicInformationView,
    FamilyCategoryView,
    FamilyMemberDetailView,
    FamilyMemberView,
    OTPRequestView,
    PhoneOTPLoginView,
    PhoneOTPRegisterView,
    SessionTokenView,
    UsernamePasswordLoginView,
    UsernamePasswordRegisterView,
)


@api_view(['GET'])
def auth_api_root(request):
    return Response(
        {
            'register': request.build_absolute_uri('/api/auth/register/'),
            'request_otp': request.build_absolute_uri('/api/auth/request-otp/'),
            'register_phone': request.build_absolute_uri('/api/auth/register-phone/'),
            'login_password': request.build_absolute_uri('/api/auth/login/password/'),
            'login_otp': request.build_absolute_uri('/api/auth/login/otp/'),
            'session': request.build_absolute_uri('/api/auth/session/'),
            'token_refresh': request.build_absolute_uri('/api/auth/token/refresh/'),
            'basic_information': request.build_absolute_uri('/api/auth/basic-information/'),
            'family_categories': request.build_absolute_uri('/api/auth/family-categories/'),
            'family_members': request.build_absolute_uri('/api/auth/family-members/'),
        }
    )


urlpatterns = [
    path('', auth_api_root, name='auth-api-root'),
    path('register/', UsernamePasswordRegisterView.as_view(), name='register'),
    path('request-otp/', OTPRequestView.as_view(), name='request-otp'),
    path('register-phone/', PhoneOTPRegisterView.as_view(), name='register-phone'),
    path('login/password/', UsernamePasswordLoginView.as_view(), name='login-password'),
    path('login/otp/', PhoneOTPLoginView.as_view(), name='login-otp'),
    path('session/', SessionTokenView.as_view(), name='session-token'),
    path('token/refresh/', AuthTokenRefreshView.as_view(), name='token-refresh'),
    path('basic-information/', BasicInformationView.as_view(), name='basic-information'),
    path('family-categories/', FamilyCategoryView.as_view(), name='family-categories'),
    path('family-members/', FamilyMemberView.as_view(), name='family-members'),
    path('family-members/<int:member_id>/', FamilyMemberDetailView.as_view(), name='family-member-detail'),
]
