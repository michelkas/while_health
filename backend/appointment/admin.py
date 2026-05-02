from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('patient', 'staff', 'date', 'time', 'accept', 'created_at')
    list_display_links = ('patient',)
    list_per_page = 25
    list_select_related = ('patient', 'staff', 'staff__user')
    
    # Search and filtering
    search_fields = ('patient__first_name', 'patient__last_name', 'patient__email', 'patient__contact', 'staff__user__first_name', 'staff__user__last_name')
    list_filter = ('accept', 'date', 'staff__departement')
    date_hierarchy = 'date'
    
    # Fields and organization
    fieldsets = (
        ('Appointment Information', {
            'fields': ('patient', 'staff', 'date', 'time')
        }),
        ('Time Service', {
            'fields': ('time_service',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('accept',),
        }),
    )
    readonly_fields = ('created_at',)
    
    # Autocomplete
    autocomplete_fields = ('patient', 'staff', 'time_service')
    
    # Actions
    actions = ['approve_appointments', 'reject_appointments']
    
    # Icons
    icon = 'fas fa-calendar-check'
    
    # List editable for quick status change
    list_editable = ('accept',)
    
    # Ordering
    ordering = ('-date', '-time')
    
    def approve_appointments(self, request, queryset):
        queryset.update(accept=True)
        self.message_user(request, f"{queryset.count()} appointment(s) approved.")
    approve_appointments.short_description = "Approve selected appointments"
    
    def reject_appointments(self, request, queryset):
        queryset.update(accept=False)
        self.message_user(request, f"{queryset.count()} appointment(s) rejected.")
    reject_appointments.short_description = "Reject selected appointments"
