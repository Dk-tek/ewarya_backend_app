from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    otp_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.username


class FamilyCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self) -> str:
        return self.name


class FamilyMember(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='family_members')
    category = models.ForeignKey(FamilyCategory, on_delete=models.PROTECT, related_name='family_members')
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'{self.name} ({self.category.name})'
