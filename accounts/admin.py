from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import FamilyCategory, FamilyMember, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            'Additional Information',
            {
                'fields': (
                    'phone_number',
                    'age',
                    'gender',
                    'date_of_birth',
                    'address',
                    'otp_verified',
                    'profile_completed',
                )
            },
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'Additional Information',
            {
                'fields': (
                    'phone_number',
                    'email',
                )
            },
        ),
    )
    list_display = ('id', 'username', 'email', 'phone_number', 'age', 'otp_verified', 'profile_completed', 'is_staff')


@admin.register(FamilyCategory)
class FamilyCategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'category', 'age', 'gender', 'phone_number')
    list_filter = ('category', 'gender')
    search_fields = ('name', 'phone_number', 'user__username')
