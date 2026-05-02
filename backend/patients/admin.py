from django import forms
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from staff.models import Staff
from .forms import ConsultationForm
from .models import Consultation, MedicalHistory, Patients, Prescription, TransferedPatient, VitalSign


class VitalSignInline(admin.TabularInline):
    model = VitalSign
    extra = 1
    min_num = 0
    max_num = 20
    can_delete = True
    show_change_link = True
    fields = ('temperature', 'heart_rate', 'oxygen_saturation', 'blood_pressure', 'pulse', 'respiration_rate', 'date_recorded')
    readonly_fields = ('date_recorded',)
    verbose_name = 'Vital Sign'
    verbose_name_plural = 'Vital Signs'


class MedicalHistoryInline(admin.TabularInline):
    model = MedicalHistory
    extra = 1
    min_num = 0
    max_num = 20
    can_delete = True
    show_change_link = True
    fields = ('chronic_diseases', 'allergies', 'long_term_treatments', 'lifestyle_habits', 'family_history', 'date_recorded')
    readonly_fields = ('date_recorded',)
    verbose_name = 'Medical History'
    verbose_name_plural = 'Medical Histories'


class ConsultationInline(admin.TabularInline):
    model = Consultation
    form = ConsultationForm
    extra = 1
    min_num = 0
    max_num = 50
    can_delete = True
    show_change_link = True
    fields = ('reason_for_consultation', 'diagnosis', 'date_recorded')
    readonly_fields = ('date_recorded',)
    verbose_name = 'Consultation'
    verbose_name_plural = 'Consultations'
 
@admin.register(VitalSign)
class VitalSignAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('patient_link', 'date_recorded', 'temperature', 'heart_rate', 'oxygen_saturation', 'blood_pressure')
    list_display_links = ('patient_link',)
    list_per_page = 25
    list_select_related = ('patient',)
    
    # Search and filtering
    search_fields = ('patient__name', 'patient__first_name')
    list_filter = ('date_recorded', 'patient__sexe')
    date_hierarchy = 'date_recorded'
    
    # Fields and organization
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient',)
        }),
        ('Vital Signs', {
            'fields': ('temperature', 'heart_rate', 'oxygen_saturation', 'blood_pressure', 'pulse', 'respiration_rate')
        }),
    )
    readonly_fields = ('date_recorded',)
    
    # Icons
    icon = 'fas fa-heartbeat'
    
    # Ordering
    ordering = ('-date_recorded',)
    
    # Additional methods
    def patient_link(self, obj):
        if obj.patient:
            url = reverse(f'admin:patients_patients_change', args=[obj.patient.pk])
            return format_html('<a href="{}">{}</a>', url, obj.patient.full_name)
        return '-'
    patient_link.short_description = 'Patient'


@admin.register(TransferedPatient)
class TransferedPatientAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('patient_link', 'transfer_date', 'reason', 'receiving_institution')
    list_display_links = ('patient_link',)
    list_per_page = 25
    list_select_related = ('patient',)
    
    # Search and filtering
    search_fields = ('patient__name', 'patient__first_name', 'reason', 'receiving_institution')
    list_filter = ('transfer_date',)
    date_hierarchy = 'transfer_date'
    
    # Fields and organization
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient',)
        }),
        ('Transfer Details', {
            'fields': ('reason', 'receiving_institution')
        }),
    )
    readonly_fields = ('transfer_date',)
    
    # Icons
    icon = 'fas fa-share-square'
    
    # Additional methods
    def patient_link(self, obj):
        if obj.patient:
            url = reverse(f'admin:patients_patients_change', args=[obj.patient.pk])
            return format_html('<a href="{}">{}</a>', url, obj.patient.full_name)
        return '-'
    patient_link.short_description = 'Patient'


@admin.register(MedicalHistory)
class MedicalHistoryAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('patient_link', 'date_recorded', 'chronic_diseases', 'allergies')
    list_display_links = ('patient_link',)
    list_per_page = 25
    list_select_related = ('patient',)
    
    # Search and filtering
    search_fields = ('patient__name', 'patient__first_name', 'chronic_diseases', 'allergies')
    list_filter = ('date_recorded',)
    date_hierarchy = 'date_recorded'
    
    # Fields and organization
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient',)
        }),
        ('Medical History', {
            'fields': ('chronic_diseases', 'allergies', 'long_term_treatments', 'lifestyle_habits', 'family_history')
        }),
    )
    readonly_fields = ('date_recorded',)
    
    # Icons
    icon = 'fas fa-file-medical'
    
    # Additional methods
    def patient_link(self, obj):
        if obj.patient:
            url = reverse(f'admin:patients_patients_change', args=[obj.patient.pk])
            return format_html('<a href="{}">{}</a>', url, obj.patient.full_name)
        return '-'
    patient_link.short_description = 'Patient'


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1
    min_num = 0
    max_num = 10
    can_delete = True
    show_change_link = True
    fields = ('medication_name', 'dosage_value', 'frequency', 'duration')
    # date_recorded is auto-populated, not editable in inline
    verbose_name = 'Prescription'
    verbose_name_plural = 'Prescriptions'


@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('patient_link', 'doctor_link', 'reason_for_consultation', 'date_recorded')
    list_display_links = ('patient_link',)
    list_per_page = 25
    list_select_related = ('patient', 'doctor')
    
    # Search and filtering
    search_fields = ('patient__name', 'patient__first_name', 'reason_for_consultation', 'diagnosis')
    search_help = '<p>Search by patient or diagnosis</p>'
    list_filter = ('date_recorded',)
    date_hierarchy = 'date_recorded'
    
    # Fields and organization
    fieldsets = (
        ('Consultation Information', {
            'fields': ('patient', 'reason_for_consultation')
        }),
        ('Diagnosis', {
            'fields': ('diagnosis',),
        }),
    )
    readonly_fields = ('date_recorded',)
    
    # Inlines
    inlines = [PrescriptionInline]
    
    # Icons
    icon = 'fas fa-stethoscope'
    
    # Additional methods
    def patient_link(self, obj):
        if obj.patient:
            url = reverse(f'admin:patients_patients_change', args=[obj.patient.pk])
            return format_html('<a href="{}">{}</a>', url, obj.patient.full_name)
        return '-'
    patient_link.short_description = 'Patient'
    
    def doctor_link(self, obj):
        if obj.doctor and obj.doctor.user:
            url = reverse(f'admin:core_user_change', args=[obj.doctor.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.doctor.user.get_full_name())
        return '-'
    doctor_link.short_description = 'Doctor'

    def save_model(self, request, obj, form, change):
        if not obj.doctor and request.user.is_authenticated:
            try:
                obj.doctor = request.user.staff_profile
            except Staff.DoesNotExist:
                pass
        super().save_model(request, obj, form, change)


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    # Display settings
    list_display = ('consultation_link', 'medication_name', 'dosage_value', 'frequency', 'duration', 'date_recorded')
    list_display_links = ('medication_name',)
    list_per_page = 25
    list_select_related = ('consultation', 'consultation__patient')
    
    # Search and filtering
    search_fields = ('medication_name', 'consultation__patient__name', 'dosage_value')
    list_filter = ('date_recorded',)
    date_hierarchy = 'date_recorded'
    
    # Fields and organization
    fieldsets = (
        ('Prescription Details', {
            'fields': ('consultation', 'medication_name', 'dosage_value', 'frequency', 'duration')
        }),
    )
    readonly_fields = ('date_recorded',)
    
    # Icons
    icon = 'fas fa-pills'
    
    # Additional methods
    def consultation_link(self, obj):
        if obj.consultation:
            url = reverse(f'admin:patients_consultation_change', args=[obj.consultation.pk])
            patient = obj.consultation.patient
            patient_name = patient.full_name if patient else "Unknown"
            return format_html('<a href="{}">{}</a>', url, patient_name)
        return '-'
    consultation_link.short_description = 'Consultation'

  

@admin.register(Patients)
class PatientsAdmin(admin.ModelAdmin):
    model = Patients
    # Display settings
    list_display = ('first_name', 'last_name', 'full_name', 'sexe', 'contact', 'email', 'registered_at')
    list_display_links = ('first_name',)
    list_per_page = 25
        
    # Inlines
    inlines = [VitalSignInline, MedicalHistoryInline, ConsultationInline]
    # Search and filtering
    search_fields = ('first_name', 'last_name', 'email', 'contact')
    search_help = '<p>Search by name, email, or contact</p>'
    list_filter = ('sexe', 'transfered', 'registered_at')
    date_hierarchy = 'registered_at'
    
    # Fields and organization
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'sexe', 'email')
        }),
        ('Contact Information', {
            'fields': ('contact', 'adress')
        }),
        ('Guardian Information', {
            'fields': ('tutor', 'tutor_contact', 'tutor_adress'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('transfered',),
        }),
    )
    readonly_fields = ('registered_at',)
    
    # Actions
    actions = ['transfer_patients', 'mark_active']
    
    # Icons
    icon = 'fas fa-user-injured'

    
    # Ordering
    ordering = ('-registered_at',)
    
    def transfer_patients(self, request, queryset):
        queryset.update(transfered=True)
        self.message_user(request, f"{queryset.count()} patient(s) marked as transferred.")
    transfer_patients.short_description = "Transfer selected patients"
    
    def mark_active(self, request, queryset):
        queryset.update(transfered=False)
        self.message_user(request, f"{queryset.count()} patient(s) marked as active.")
    mark_active.short_description = "Mark as active"

    def save_formset(self, request, form, formset, change):
        if formset.model is Consultation:
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.doctor and request.user.is_authenticated:
                    try:
                        instance.doctor = request.user.staff_profile
                    except Staff.DoesNotExist:
                        pass
                instance.save()
            formset.save_m2m()
        else:
            super().save_formset(request, form, formset, change)

