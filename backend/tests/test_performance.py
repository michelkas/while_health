# ============================================
# While Health - Tests Automatisés
# ============================================

import pytest
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection

from patients.models import Patients, Consultation, VitalSign
from appointment.models import Appointment
from staff.models import Staff

User = get_user_model()


class PerformanceTestCase(TestCase):
    """Tests de performance pour les optimisations."""

    def setUp(self):
        # Créer des données de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.staff = Staff.objects.create(
            user=self.user,
            first_name='Test',
            last_name='Doctor',
            role=Staff.Role.DOCTOR,
            is_active=True,
            is_verified=True
        )

    def test_dashboard_cache_performance(self):
        """Test que le cache du dashboard fonctionne."""
        from core.views import CACHE_KEYS

        # Clear cache
        cache.delete(CACHE_KEYS['dashboard_stats'])

        # First request should cache
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

        # Check cache was set
        cached_data = cache.get(CACHE_KEYS['dashboard_stats'])
        self.assertIsNotNone(cached_data)

    def test_patient_list_aggregation(self):
        """Test que l'agrégation des stats patients fonctionne."""
        # Create test patients
        Patients.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            sexe='M'
        )
        Patients.objects.create(
            first_name='Jane',
            last_name='Doe',
            email='jane@example.com',
            sexe='F',
            transfered=True
        )

        # Test aggregation query
        from django.db.models import Count, Q
        stats = Patients.objects.aggregate(
            total=Count('id'),
            transferred=Count('id', filter=Q(transfered=True)),
            active=Count('id', filter=Q(transfered=False))
        )

        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['transferred'], 1)
        self.assertEqual(stats['active'], 1)

    def test_n_plus_one_prevention(self):
        """Test que les requêtes N+1 sont évitées."""
        # Create test data
        patient = Patients.objects.create(
            first_name='Test',
            last_name='Patient',
            email='test@example.com'
        )

        consultations = []
        for i in range(5):
            consultations.append(
                Consultation.objects.create(
                    patient=patient,
                    doctor=self.staff,
                    reason_for_consultation=f'Reason {i}'
                )
            )

        # Test optimized query
        with self.assertNumQueries(1):  # Should be 1 query with prefetch
            consultations = Consultation.objects.filter(
                patient=patient
            ).select_related('patient', 'doctor__user')

            for consultation in consultations:
                _ = consultation.patient.first_name
                _ = consultation.doctor.user.get_full_name()


class SecurityTestCase(TestCase):
    """Tests de sécurité."""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_patient_lookup_rate_limiting(self):
        """Test que le rate limiting fonctionne sur patient_lookup."""
        self.client.login(username='testuser', password='testpass123')

        # Make multiple requests quickly
        for i in range(15):
            response = self.client.post(
                reverse('patient_lookup'),
                {'contact': '+243123456789'}
            )

        # Should be rate limited after 10 requests
        self.assertEqual(response.status_code, 429)  # Too Many Requests

    def test_permission_required_on_sensitive_views(self):
        """Test que les vues sensibles nécessitent des permissions."""
        # Create user without permissions
        regular_user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='testpass123'
        )

        self.client.login(username='regular', password='testpass123')

        # Try to access admin dashboard
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_sql_injection_prevention(self):
        """Test que les injections SQL sont empêchées."""
        self.client.login(username='testuser', password='testpass123')

        # Try SQL injection in search
        malicious_query = "'; DROP TABLE patients; --"
        response = self.client.get(
            reverse('patient_list') + f'?q={malicious_query}'
        )

        # Should not crash and table should still exist
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Patients.objects.exists())


class ValidationTestCase(TestCase):
    """Tests de validation des données."""

    def test_patient_uniqueness_validation(self):
        """Test que l'unicité email/contact est validée."""
        # Create first patient
        Patients.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            contact='+243123456789'
        )

        # Try to create duplicate
        with self.assertRaises(Exception):  # ValidationError
            Patients.objects.create(
                first_name='Jane',
                last_name='Doe',
                email='john@example.com',  # Duplicate email
                contact='+243987654321'
            )

    def test_appointment_conflict_validation(self):
        """Test que les conflits de rendez-vous sont détectés."""
        from datetime import date, time

        patient = Patients.objects.create(
            first_name='Test',
            last_name='Patient',
            email='test@example.com'
        )

        # Create first appointment
        appointment1 = Appointment.objects.create(
            patient=patient,
            staff=self.staff,
            date=date.today(),
            time=time(10, 0),
            accept=True
        )

        # Try to create conflicting appointment
        with self.assertRaises(Exception):  # ValidationError
            Appointment.objects.create(
                patient=patient,
                staff=self.staff,
                date=date.today(),
                time=time(10, 0),  # Same time slot
                accept=True
            )


class AsyncTaskTestCase(TestCase):
    """Tests des tâches asynchrones."""

    def setUp(self):
        self.patient = Patients.objects.create(
            first_name='Test',
            last_name='Patient',
            email='test@example.com'
        )

    @override_settings(CELERY_ALWAYS_EAGER=True)  # Run tasks synchronously for testing
    def test_pdf_generation_task(self):
        """Test que la génération PDF fonctionne."""
        from core.tasks import generate_patient_report_pdf

        # This would normally be run asynchronously
        result = generate_patient_report_pdf(self.patient.id)

        # Should return PDF data
        self.assertIsInstance(result, bytes)
        self.assertGreater(len(result), 0)

    @override_settings(CELERY_ALWAYS_EAGER=True)
    def test_monthly_stats_task(self):
        """Test que les stats mensuelles fonctionnent."""
        from core.tasks import generate_monthly_statistics

        result = generate_monthly_statistics()

        # Should return stats dict
        self.assertIsInstance(result, dict)
        self.assertIn('total_patients', result)