from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import About, Contact, Emergency, EmergencyInfo, Hero, Service


@admin.register(Hero)
class HeroAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('title', 'subtitle', 'description')
    list_display_links = ('title',)
    list_per_page = 10
    
    # Search and filtering
    search_fields = ('title', 'subtitle', 'description')
    
    # Fields and organization
    fieldsets = (
        ('Hero Information', {
            'fields': ('title', 'subtitle', 'description', 'image')
        }),
    )
    
    # Icons
    icon = 'fas fa-image'
    
    # Additional methods
    def has_add_permission(self, request):
        # Only allow one hero
        if Hero.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(About)
class AboutAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('title', 'subtitle', 'year', 'location')
    list_display_links = ('title',)
    list_per_page = 10
    
    # Search and filtering
    search_fields = ('title', 'subtitle', 'description', 'location')
    list_filter = ('year',)
    
    # Fields and organization
    fieldsets = (
        ('About Information', {
            'fields': ('title', 'subtitle', 'year', 'goal', 'location')
        }),
        ('Descriptions', {
            'fields': ('description', 'compassionate_care', 'care_quality'),
            'classes': ('collapse',)
        }),
        ('Image', {
            'fields': ('image',),
        }),
    )
    
    # Icons
    icon = 'fas fa-info-circle'
    
    # Additional methods
    def has_add_permission(self, request):
        # Only allow one about
        if About.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('title', 'department_link', 'icon', 'created_at')
    list_display_links = ('title',)
    list_per_page = 25
    list_select_related = ('departement',)
    
    # Search and filtering
    search_fields = ('title', 'description', 'short_description')
    list_filter = ('departement', 'created_at')
    date_hierarchy = 'created_at'
    
    # Fields and organization
    fieldsets = (
        ('Service Information', {
            'fields': ('title', 'departement', 'description', 'short_description')
        }),
        ('Icon', {
            'fields': ('icon',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    
    # Icons
    icon = 'fas fa-concierge-bell'
    
    # Additional methods
    def department_link(self, obj):
        if obj.departement:
            url = reverse(f'admin:staff_departement_change', args=[obj.departement.pk])
            return format_html('<a href="{}">{}</a>', url, obj.departement.name)
        return '-'
    department_link.short_description = 'Department'


@admin.register(EmergencyInfo)
class EmergencyInfoAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('title', 'phone', 'address', 'operation_time')
    list_display_links = ('title',)
    list_per_page = 10
    
    # Search and filtering
    search_fields = ('title', 'phone', 'address')
    
    # Fields and organization
    fieldsets = (
        ('Emergency Info', {
            'fields': ('title', 'phone', 'address', 'operation_time')
        }),
    )
    
    # Icons
    icon = 'fas fa-ambulance'
    
    # Additional methods
    def has_add_permission(self, request):
        # Only allow one emergency info
        if EmergencyInfo.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(Emergency)
class EmergencyAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('title', 'phone', 'description')
    list_display_links = ('title',)
    list_per_page = 10
    
    # Search and filtering
    search_fields = ('title', 'phone', 'description')
    
    # Fields and organization
    fieldsets = (
        ('Emergency', {
            'fields': ('title', 'phone', 'description')
        }),
    )
    
    # Icons
    icon = 'fas fa-exclamation-triangle'
    
    # Additional methods
    def has_add_permission(self, request):
        # Only allow one emergency
        if Emergency.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('name', 'phone', 'email', 'address', 'operation_days_time')
    list_display_links = ('name',)
    list_per_page = 10
    
    # Search and filtering
    search_fields = ('name', 'phone', 'email', 'address')
    
    # Fields and organization
    fieldsets = (
        ('Hospital Information', {
            'fields': ('name', 'operation_days_time', 'phone', 'email', 'address')
        }),
        ('Social Media', {
            'fields': ('facebook', 'twitter', 'instagram', 'linkedin'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_at',)
    
    # Icons
    icon = 'fas fa-hospital-o'
    
    # Additional methods
    def has_add_permission(self, request):
        # Only allow one contact
        if Contact.objects.exists():
            return False
        return super().has_add_permission(request)
