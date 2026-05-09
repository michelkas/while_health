from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from django.urls import reverse
from django.utils.html import format_html


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # Display settings
    list_display = ('email', 'username', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'avatar_preview')
    list_display_links = ('email',)
    list_per_page = 25
    
    # Search and filtering
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    
    # Fields and organization
    fieldsets = (
      
        ('Personal Information', {
            'fields': ('email', 'first_name', 'last_name', 'avatar', 'avatar_preview', 'username')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
          (None, {
            'fields': ('password',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
      
    )
    readonly_fields = ('last_login', 'date_joined', 'avatar_preview', 'username')
    add_fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'first_name', 'last_name')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
    )
    
    # Ordering
    ordering = ('-date_joined',)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if not request.user.is_superuser:
            # For non-superusers, remove the password fieldset
            fieldsets = [fs for fs in fieldsets if fs[1]['fields'] != ('password',)]
        return fieldsets

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover;" />', obj.avatar.url)
        return "No avatar"
    avatar_preview.short_description = 'Avatar'
    
    # Actions
    actions = ['approve_users', 'deactivate_users']
    
    # Icons
    icon = 'fas fa-user-md'
    
    def approve_users(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} user(s) approved.")
    approve_users.short_description = "Approve selected users"
    
    def deactivate_users(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} user(s) deactivated.")
    deactivate_users.short_description = "Deactivate selected users"

    def change_password_link(self, obj):
        if obj.pk:
            url = reverse('admin:auth_user_password_change', args=[obj.pk])
            return format_html(
                '<a href="{}" class="btn btn-danger btn-sm jazmin-btn" style="background:#ba2121; color:white;">'
                '<i class="fas fa-key"></i> Modifier le mot de passe</a>',
                url
            )
        return "-"
    change_password_link.short_description = ("Mot de passe")