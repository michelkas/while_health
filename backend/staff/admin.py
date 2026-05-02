from django.contrib import admin
from .forms import TimeServiceForm
from .models import Departement, Staff, TimeService


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('name', 'created_at')
    list_display_links = ('name',)
    list_per_page = 20
    
    # Search and filtering
    search_fields = ('name', 'description')
    list_filter = ('created_at',)
    
    # Fields and organization
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'image')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
    )
    prepopulated_fields = {'slug': ('name',)}
    
    # Icons
    icon = 'fas fa-building'


class TimeServiceInline(admin.TabularInline):
    model = TimeService
    extra = 1
    fields = ('service_day', 'open_time', 'close_time')
    verbose_name = 'Time Service'
    verbose_name_plural = 'Time Services'
    classes = ('collapse',)


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('first_name', 'last_name', 'role', 'specialty', 'departement', 'is_active', 'is_verified')
    list_display_links = ('first_name',)
    list_per_page = 25
    list_select_related = ('user', 'departement')
    
    # Search and filtering
    search_fields = ('user__first_name', 'user__last_name', 'name', 'first_name', 'last_name')
    list_filter = ('role', 'specialty', 'is_active', 'is_verified', 'departement', 'created_at')
    date_hierarchy = 'created_at'
    
    # Fields and organization
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'name', 'first_name', 'last_name')
        }),
        ('Professional Information', {
            'fields': ('role', 'specialty', 'departement', 'experience_years')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified'),
            'classes': ('collapse',)
        }),
        ('Social Links', {
            'fields': ('twitter', 'facebook', 'instagram', 'linkedin'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at', 'slug')
    prepopulated_fields = {'slug': ('first_name', 'last_name')}
    
    # Inlines
    inlines = [TimeServiceInline]
    
    # Autocomplete
    autocomplete_fields = ('departement', 'user')
    
    # Actions
    actions = ['approve_staff', 'deactivate_staff', 'verify_staff']
    
    # Icons
    icon = 'fas fa-user-md'
    
    # List editable for quick changes
    list_editable = ('is_active', 'is_verified')
    
    # Ordering
    ordering = ('-created_at',)
    
    def approve_staff(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"{queryset.count()} staff member(s) activated.")
    approve_staff.short_description = "Activate selected staff"
    
    def deactivate_staff(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"{queryset.count()} staff member(s) deactivated.")
    deactivate_staff.short_description = "Deactivate selected staff"
    
    def verify_staff(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, f"{queryset.count()} staff member(s) verified.")
    verify_staff.short_description = "Verify selected staff"


@admin.register(TimeService)
class TimeServiceAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('staff', 'service_day', 'open_time', 'close_time')
    list_display_links = ('staff',)
    list_per_page = 25
    list_select_related = ('staff', 'staff__user')
    
    # Search and filtering
    search_fields = ('staff__user__first_name', 'staff__user__last_name', 'service_day')
    list_filter = ('service_day', 'staff__departement')
    
    # Form settings
    form = TimeServiceForm
    
    # Ordering
    ordering = ('staff', 'service_day')
    
    # Icons
    icon = 'fas fa-clock'
