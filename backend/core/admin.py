from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    list_display_links = ('email',)
    list_per_page = 25
    
    # Search and filtering
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'is_superuser')
    
    # Fields and organization
    fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'first_name', 'last_name', 'avatar')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('last_login', 'date_joined')
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

