from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenRefreshView

from .models import FamilyCategory
from .serializers import (
    BasicInformationSerializer,
    FamilyCategorySerializer,
    FamilyMemberSerializer,
    OTPRequestSerializer,
    PhoneOTPLoginSerializer,
    PhoneOTPRegisterSerializer,
    UsernamePasswordLoginSerializer,
    UsernamePasswordRegisterSerializer,
)


class UsernamePasswordRegisterView(APIView):
    def post(self, request):
        serializer = UsernamePasswordRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'message': 'User registered successfully.',
                'user': BasicInformationSerializer(user).data,
                'tokens': serializer.get_tokens(user),
            },
            status=status.HTTP_201_CREATED,
        )


class OTPRequestView(APIView):
    def post(self, request):
        serializer = OTPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                'message': 'OTP sent successfully.',
                'phone_number': serializer.validated_data['phone_number'],
                'otp': serializer.get_default_otp(),
                'note': 'SMS gateway is not configured, so the default OTP is returned for development.',
            },
            status=status.HTTP_200_OK,
        )


class PhoneOTPRegisterView(APIView):
    def post(self, request):
        serializer = PhoneOTPRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'message': 'Phone number registered successfully.',
                'user': BasicInformationSerializer(user).data,
                'tokens': serializer.get_tokens(user),
            },
            status=status.HTTP_201_CREATED,
        )


class UsernamePasswordLoginView(APIView):
    def post(self, request):
        serializer = UsernamePasswordLoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class PhoneOTPLoginView(APIView):
    def post(self, request):
        serializer = PhoneOTPLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class BasicInformationView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = BasicInformationSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = BasicInformationSerializer(request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'message': 'Basic information updated successfully.',
                'user': serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = BasicInformationSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'message': 'Basic information updated successfully.',
                'user': serializer.data,
            },
            status=status.HTTP_200_OK,
        )


class AuthTokenRefreshView(TokenRefreshView):
    pass


class FamilyCategoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        categories = FamilyCategory.objects.all().order_by('name')
        serializer = FamilyCategorySerializer(categories, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FamilyCategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'message': 'Family category created successfully.',
                'category': serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class FamilyMemberView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        family_members = request.user.family_members.select_related('category').order_by('-id')
        serializer = FamilyMemberSerializer(family_members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FamilyMemberSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'message': 'Family member added successfully.',
                'family_member': serializer.data,
            },
            status=status.HTTP_201_CREATED,
        )


class FamilyMemberDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, request, member_id):
        try:
            return request.user.family_members.select_related('category').get(id=member_id)
        except request.user.family_members.model.DoesNotExist:
            return None

    def get(self, request, member_id):
        family_member = self.get_object(request, member_id)
        if not family_member:
            return Response({'detail': 'Family member not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FamilyMemberSerializer(family_member)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, member_id):
        family_member = self.get_object(request, member_id)
        if not family_member:
            return Response({'detail': 'Family member not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = FamilyMemberSerializer(
            family_member,
            data=request.data,
            partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                'message': 'Family member updated successfully.',
                'family_member': serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, member_id):
        family_member = self.get_object(request, member_id)
        if not family_member:
            return Response({'detail': 'Family member not found.'}, status=status.HTTP_404_NOT_FOUND)

        family_member.delete()
        return Response({'message': 'Family member deleted successfully.'}, status=status.HTTP_200_OK)
