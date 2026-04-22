from django.conf import settings
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import FamilyCategory, FamilyMember, User


class TokenMixin:
    @staticmethod
    def get_tokens(user: User) -> dict[str, str]:
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class OTPRequestSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value: str) -> str:
        return value.strip()

    @staticmethod
    def get_default_otp() -> str:
        return settings.DEFAULT_OTP


class UsernamePasswordRegisterSerializer(serializers.Serializer, TokenMixin):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    phone_number = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True, allow_null=True)

    def validate_username(self, value: str) -> str:
        value = value.strip()
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Username is already registered.')
        return value

    def validate_phone_number(self, value: str) -> str:
        value = value.strip()
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Phone number is already registered.')
        return value

    def validate_email(self, value: str) -> str:
        if not value:
            return None
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email is already registered.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(
            **validated_data,
            is_staff=True,
            otp_verified=False,
            profile_completed=False,
        )
        user.set_password(password)
        user.save()
        return user


class PhoneOTPRegisterSerializer(serializers.Serializer, TokenMixin):
    phone_number = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=10)

    def validate_phone_number(self, value: str) -> str:
        value = value.strip()
        if User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError('Phone number is already registered.')
        return value

    def validate_otp(self, value: str) -> str:
        if value.strip() != settings.DEFAULT_OTP:
            raise serializers.ValidationError('Invalid OTP.')
        return value.strip()

    def create(self, validated_data):
        phone_number = validated_data['phone_number']
        username = self._generate_username(phone_number)
        user = User.objects.create(
            username=username,
            phone_number=phone_number,
            otp_verified=True,
            profile_completed=False,
        )
        user.set_unusable_password()
        user.save()
        return user

    @staticmethod
    def _generate_username(phone_number: str) -> str:
        digits = ''.join(ch for ch in phone_number if ch.isdigit())
        base_username = f"user_{digits or 'mobile'}"
        username = base_username
        counter = 1

        while User.objects.filter(username=username).exists():
            counter += 1
            username = f'{base_username}_{counter}'

        return username


class UsernamePasswordLoginSerializer(serializers.Serializer, TokenMixin):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get('request'),
            username=attrs.get('username'),
            password=attrs.get('password'),
        )
        if not user:
            raise serializers.ValidationError({'detail': 'Invalid username or password.'})

        return {
            'message': 'Login successful.',
            'user': BasicInformationSerializer(user).data,
            'tokens': self.get_tokens(user),
            'raw_user': user,
        }


class PhoneOTPLoginSerializer(serializers.Serializer, TokenMixin):
    phone_number = serializers.CharField(max_length=20)
    otp = serializers.CharField(max_length=10)

    def validate(self, attrs):
        phone_number = attrs.get('phone_number', '').strip()
        otp = attrs.get('otp', '').strip()

        if otp != settings.DEFAULT_OTP:
            raise serializers.ValidationError({'detail': 'Invalid OTP.'})

        try:
            user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist as exc:
            raise serializers.ValidationError({'detail': 'User with this phone number does not exist.'}) from exc

        if not user.otp_verified:
            user.otp_verified = True
            user.save(update_fields=['otp_verified'])

        return {
            'message': 'Login successful.',
            'user': BasicInformationSerializer(user).data,
            'tokens': self.get_tokens(user),
        }


class BasicInformationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'password',
            'email',
            'phone_number',
            'first_name',
            'last_name',
            'age',
            'gender',
            'date_of_birth',
            'address',
            'otp_verified',
            'profile_completed',
        )
        read_only_fields = ('id', 'otp_verified', 'profile_completed')

    def validate_email(self, value):
        if not value:
            return None

        normalized = value.strip().lower()
        qs = User.objects.filter(email=normalized).exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError('Email is already registered.')
        return normalized

    def validate_phone_number(self, value):
        normalized = value.strip()
        qs = User.objects.filter(phone_number=normalized).exclude(id=self.instance.id)
        if qs.exists():
            raise serializers.ValidationError('Phone number is already registered.')
        return normalized

    def validate(self, attrs):
        password = attrs.get('password')
        if password and self.instance and self.instance.has_usable_password():
            raise serializers.ValidationError({'password': 'Password is already set for this account.'})
        return attrs

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)

        completion_fields = ['first_name', 'last_name', 'email']
        user.profile_completed = all(bool(getattr(user, field)) for field in completion_fields)
        update_fields = ['profile_completed']
        if password:
            update_fields.append('password')
        user.save(update_fields=update_fields)
        return user


class FamilyCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FamilyCategory
        fields = ('id', 'name')

    def validate_name(self, value: str) -> str:
        normalized = value.strip().lower()
        if FamilyCategory.objects.filter(name__iexact=normalized).exclude(id=getattr(self.instance, 'id', None)).exists():
            raise serializers.ValidationError('Family category already exists.')
        return normalized


class FamilyMemberSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        source='category',
        queryset=FamilyCategory.objects.all(),
    )
    category = FamilyCategorySerializer(read_only=True)

    class Meta:
        model = FamilyMember
        fields = (
            'id',
            'user_id',
            'name',
            'category_id',
            'category',
            'age',
            'gender',
            'phone_number',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'user_id', 'category', 'created_at', 'updated_at')

    def validate_phone_number(self, value: str) -> str:
        return value.strip()

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
