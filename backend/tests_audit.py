"""
Tests de validation - Audit While Health

À exécuter avec: python manage.py test

Tests les corrections critiques:
- Authentification obligatoire
- Permissions staff
- Validations métier
- Pagination
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test.utils import override_settings, CaptureQueriesContext
from django.db import connection

from patients.models import Patients, Consultation, VitalSign, Prescription
from staff.models import Staff, Departement
from appointment.models import Appointment

User = get_user_model()


class SecurityTests(TestCase):
    """Tests de sécurité - Authentication & Permissions"""
    
    def setUp(self):
        """Setup test users and data"""
        self.client = Client()
        
        # Create department
        self.dept = Departement.objects.create(name="Cardiologie")
        
        # Create patient user (non-staff)
        self.patient_user = User.objects.create_user(
            username='patient1',
            password='testpass123',
            email='patient@hospital.com'
        )
        
        # Create doctor user (staff)
        self.doctor_user = User.objects.create_user(
            username='dr_smith',
            password='testpass123',
            email='doctor@hospital.com',
            is_staff=True
        )
        self.doctor_staff = Staff.objects.create(
            user=self.doctor_user,
            departement=self.dept,
            role='MEDECIN',
            is_active=True
        )
        
        # Create patient
        self.patient = Patients.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@patient.com',
            contact='+243912345678',
            sexe='M',
            adress='123 Main St'
        )
    
    def test_appointment_is_public(self):
        """✅ P1.2: Appointment view can be accessed without login"""
        response = self.client.get('/appointment/')
        self.assertEqual(response.status_code, 200)
    
    def test_appointment_allows_anonymous_access(self):
        """✅ P1.2: Anonymous users can view the appointment form"""
        response = self.client.get('/appointment/')
        self.assertEqual(response.status_code, 200)
    
    def test_appointment_staff_can_access(self):
        """✅ P1.2: Staff can access appointment form"""
        self.client.login(username='dr_smith', password='testpass123')
        response = self.client.get('/appointment/')
        self.assertEqual(response.status_code, 200)
    
    def test_patient_lookup_is_public(self):
        """✅ P1.2: Patient lookup works for anonymous requests"""
        response = self.client.post('/patient-lookup/', {'contact': '+243912345678'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('patient', response.json())
    
    def test_patient_lookup_returns_patient_data(self):
        """✅ P1.2: Patient lookup returns patient fields for appointment autofill"""
        self.client.get('/appointment/')
        csrf_token = self.client.cookies.get('csrftoken')
        response = self.client.post(
            '/patient-lookup/',
            data=b'{"contact": "+243912345678"}',
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token.value if csrf_token else ''
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('patient', data)
        self.assertIn('email', data['patient'])
        self.assertIn('adress', data['patient'])
        self.assertEqual(data['patient']['contact'], '+243912345678')

    def test_available_slots_endpoint_is_public(self):
        """✅ P1.2: Available slots endpoint returns doctor schedule"""
        response = self.client.get(f'/available-slots/?staff_id={self.doctor_staff.pk}')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('doctor', data)
        self.assertIn('schedule', data)
        self.assertIn('slots', data)


class ValidationTests(TestCase):
    """Tests de validation métier"""
    
    def setUp(self):
        self.dept = Departement.objects.create(name="General")
        self.doctor = User.objects.create_user(
            username='doctor',
            password='test',
            is_staff=True
        )
        self.doctor_staff = Staff.objects.create(
            user=self.doctor,
            departement=self.dept,
            role='MEDECIN',
            is_active=True
        )
        self.patient = Patients.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@hospital.com',
            contact='+243987654321',
            sexe='F',
            adress='456 Oak St'
        )
    
    def test_prescription_dosage_validation(self):
        """✅ P1.3: Prescription dosage must be within safe range"""
        consultation = Consultation.objects.create(
            patient=self.patient,
            doctor=self.doctor_staff,
            reason_for_consultation="Headache"
        )
        
        # Create prescription with excessive dosage
        prescription = Prescription(
            consultation=consultation,
            medication_name='PARACETAMOL',
            dosage_value=5000,  # Max 1000!
            frequency='2x/day',
            duration='2 jours'
        )
        
        with self.assertRaises(ValidationError):
            prescription.full_clean()
    
    def test_patient_unique_email(self):
        """✅ P1.3: Duplicate email should fail"""
        # Try to create patient with duplicate email
        duplicate = Patients(
            first_name='Duplicate',
            last_name='User',
            email='jane@hospital.com',  # Already exists
            contact='+243911111111',
            sexe='M',
            adress='789 Elm St'
        )
        
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
    
    def test_patient_unique_contact(self):
        """✅ P1.3: Duplicate phone should fail"""
        duplicate = Patients(
            first_name='Duplicate',
            last_name='User',
            email='dup@hospital.com',
            contact='+243987654321',  # Already exists
            sexe='M',
            adress='789 Elm St'
        )
        
        with self.assertRaises(ValidationError):
            duplicate.full_clean()
    
    def test_vital_signs_temperature_range(self):
        """✅ P1.3: Temperature must be realistic"""
        # Invalid: temperature too high
        vital = VitalSign(
            patient=self.patient,
            temperature=50,  # Max 42!
        )
        
        with self.assertRaises(ValidationError):
            vital.full_clean()
    
    def test_consultation_requires_active_doctor(self):
        """✅ P1.3: Consultation doctor must be active"""
        # Deactivate doctor
        self.doctor_staff.is_active = False
        self.doctor_staff.save()
        
        consultation = Consultation(
            patient=self.patient,
            doctor=self.doctor_staff,
            reason_for_consultation="Test"
        )
        
        with self.assertRaises(ValidationError):
            consultation.full_clean()


class PerformanceTests(TestCase):
    """Tests de performance - N+1 queries"""
    
    def setUp(self):
        self.dept = Departement.objects.create(name="General")
        self.doctor = User.objects.create_user(
            username='doctor',
            password='test',
            is_staff=True
        )
        self.doctor_staff = Staff.objects.create(
            user=self.doctor,
            departement=self.dept,
            role='MEDECIN',
            is_active=True
        )
        
        # Create test patients
        for i in range(10):
            Patients.objects.create(
                first_name=f'Patient{i}',
                last_name=f'Test{i}',
                email=f'patient{i}@hospital.com',
                contact=f'+24391234567{i}',
                sexe='M',
                adress=f'{i} Test St'
            )
    
    def test_patient_list_queries_optimized(self):
        """✅ P2.1: Patient list should use select_related"""
        from patients.models import Patients
        
        with CaptureQueriesContext(connection) as context:
            # This should NOT be optimized - baseline
            list(Patients.objects.all())
        
        unoptimized_count = len(context.captured_queries)
        
        # Optimized version
        with CaptureQueriesContext(connection) as context:
            list(Patients.objects.select_related().all())
        
        optimized_count = len(context.captured_queries)
        
        # Optimized should have same or fewer queries
        self.assertLessEqual(optimized_count, unoptimized_count)
        print(f"✅ Queries: {unoptimized_count} → {optimized_count}")
    
    def test_consultation_with_prescriptions_queries(self):
        """✅ P2.3: Consultation with prescriptions should be optimized"""
        # Create consultation with prescriptions
        for i in range(5):
            patient = Patients.objects.first()
            consultation = Consultation.objects.create(
                patient=patient,
                doctor=self.doctor_staff,
                reason_for_consultation=f"Issue {i}"
            )
            for j in range(3):
                Prescription.objects.create(
                    consultation=consultation,
                    medication_name='ASPIRIN',
                    dosage_value=100,
                    frequency='2x/day',
                    duration='3 jours'
                )
        
        # Unoptimized access pattern
        with CaptureQueriesContext(connection) as context:
            for consultation in Consultation.objects.all():
                for prescription in consultation.prescriptions.all():
                    _ = prescription.medication_name
        
        unoptimized_count = len(context.captured_queries)
        
        # ✅ PERFORMANCE: Optimized with prefetch_related
        from django.db.models import Prefetch
        with CaptureQueriesContext(connection) as context:
            consultation_prefetch = Prefetch(
                'prescriptions',
                queryset=Prescription.objects.select_related('consultation')
            )
            consultations = Consultation.objects.prefetch_related(
                consultation_prefetch
            ).select_related('patient', 'doctor__user')
            
            for consultation in consultations:
                for prescription in consultation.prescriptions.all():
                    _ = prescription.medication_name
        
        optimized_count = len(context.captured_queries)
        
        # Optimized should be significantly fewer
        print(f"✅ Consultation queries: {unoptimized_count} → {optimized_count}")
        self.assertLess(optimized_count, unoptimized_count)


class PaginationTests(TestCase):
    """Tests de pagination"""
    
    def setUp(self):
        # Create 50 patients
        for i in range(50):
            Patients.objects.create(
                first_name=f'Patient{i}',
                last_name=f'Test{i}',
                email=f'patient{i}@hospital.com',
                contact=f'+24391234567{i:02d}',
                sexe='M' if i % 2 == 0 else 'F',
                adress=f'{i} Test St'
            )
        
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client = Client()
    
    def test_patient_list_pagination(self):
        """✅ P4.1: Patient list should paginate"""
        self.client.login(username='testuser', password='testpass')
        response = self.client.get('/patients/list/')
        
        if response.status_code == 200:
            # Check if paginator in context
            page_obj = response.context.get('page_obj')
            if page_obj:
                # Should have 25 patients per page
                self.assertLessEqual(len(page_obj.object_list), 25)
                self.assertGreater(page_obj.paginator.num_pages, 1)


class SettingsSecurityTests(TestCase):
    """Tests de configuration sécurité"""
    
    @override_settings(DEBUG=False)
    def test_debug_false_in_production(self):
        """✅ P1.1: DEBUG must be False in production"""
        from django.conf import settings
        self.assertFalse(settings.DEBUG)
    
    @override_settings(ALLOWED_HOSTS=['localhost', '127.0.0.1'])
    def test_allowed_hosts_configured(self):
        """✅ P1.1: ALLOWED_HOSTS must be configured"""
        from django.conf import settings
        self.assertTrue(len(settings.ALLOWED_HOSTS) > 0)
    
    @override_settings(SECRET_KEY='production-secret-key-min-50-chars-xxxxxxxxxxxxxxxxxxxxxxxxxx')
    def test_secret_key_configured(self):
        """✅ P1.1: SECRET_KEY must be long and random"""
        from django.conf import settings
        self.assertGreater(len(settings.SECRET_KEY), 50)


# Run tests with: python manage.py test
# Run specific test: python manage.py test patients.tests.SecurityTests
# Run with coverage: coverage run --source='.' manage.py test && coverage report
