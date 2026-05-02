# ============================================
# While Health - Tests de Sécurité
# ============================================

import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

from patients.models import Patients
from staff.models import Staff

User = get_user_model()


class SecurityTestSuite(TestCase):
    """Suite complète de tests de sécurité."""

    def setUp(self):
        self.client = Client()
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@whilehealth.com',
            password='admin123!',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='nurse',
            email='nurse@whilehealth.com',
            password='nurse123!'
        )

    def test_https_enforcement(self):
        """Test que HTTPS est forcé en production."""
        with self.settings(SECURE_SSL_REDIRECT=True):
            response = self.client.get('/', secure=False)
            self.assertEqual(response.status_code, 301)  # Redirect to HTTPS

    def test_secure_headers(self):
        """Test que les headers de sécurité sont présents."""
        self.client.login(username='admin', password='admin123!')
        response = self.client.get(reverse('dashboard'))

        # Check security headers
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertIn('max-age=31536000', response.get('Strict-Transport-Security', ''))

    def test_csrf_protection(self):
        """Test que la protection CSRF fonctionne."""
        # POST without CSRF token should fail
        response = self.client.post(
            reverse('patient_lookup'),
            {'contact': '+243123456789'}
        )
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_sql_injection_attempts(self):
        """Test multiple tentatives d'injection SQL."""
        injection_attempts = [
            "'; DROP TABLE patients; --",
            "' OR '1'='1",
            "admin'--",
            "1 UNION SELECT * FROM users--",
            "'; EXEC xp_cmdshell('dir') --",
        ]

        self.client.login(username='admin', password='admin123!')

        for attempt in injection_attempts:
            with self.subTest(attempt=attempt):
                response = self.client.get(
                    reverse('patient_list') + f'?q={attempt}'
                )
                # Should not crash and should return valid response
                self.assertEqual(response.status_code, 200)
                # Table should still exist
                self.assertTrue(Patients.objects.exists())

    def test_xss_prevention(self):
        """Test que les attaques XSS sont empêchées."""
        xss_payloads = [
            '<script>alert("XSS")</script>',
            '<img src=x onerror=alert("XSS")>',
            'javascript:alert("XSS")',
            '<iframe src="javascript:alert(\'XSS\')"></iframe>',
        ]

        self.client.login(username='admin', password='admin123!')

        for payload in xss_payloads:
            with self.subTest(payload=payload):
                # Try to inject in patient creation
                response = self.client.post(
                    reverse('patient_create'),
                    {
                        'first_name': payload,
                        'last_name': 'Test',
                        'email': f'test{random.randint(1,1000)}@example.com',
                        'adress': 'Test Address',
                        'sexe': 'M',
                        'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '').value
                    }
                )

                # Should either fail validation or escape the content
                if response.status_code == 200:  # Form rendered
                    content = response.content.decode()
                    # Payload should be escaped or not executed
                    self.assertNotIn('<script>', content)

    def test_rate_limiting(self):
        """Test que le rate limiting fonctionne."""
        # Make many requests quickly
        for i in range(15):
            response = self.client.post(
                reverse('patient_lookup'),
                {
                    'contact': '+243123456789',
                    'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '').value
                }
            )

        # Should be rate limited
        self.assertEqual(response.status_code, 429)

    def test_permission_escalation_prevention(self):
        """Test que l'escalade de privilèges est empêchée."""
        # Login as regular user
        self.client.login(username='nurse', password='nurse123!')

        # Try to access admin-only views
        admin_views = [
            reverse('dashboard'),
            reverse('patient_list'),
            reverse('patient_create'),
        ]

        for view in admin_views:
            with self.subTest(view=view):
                response = self.client.get(view)
                # Should redirect to login or return 403
                self.assertIn(response.status_code, [302, 403])

    def test_data_leakage_prevention(self):
        """Test qu'aucune donnée sensible n'est exposée."""
        # Create patient with sensitive data
        patient = Patients.objects.create(
            first_name='Secret',
            last_name='Patient',
            email='secret@example.com',
            contact='+243123456789',
            adress='Secret Address'
        )

        # Login as regular user
        self.client.login(username='nurse', password='nurse123!')

        # Try to access patient data
        response = self.client.get(reverse('patient_detail', args=[patient.id]))

        # Should be denied
        self.assertEqual(response.status_code, 403)

        # Check that no sensitive data is in response
        content = response.content.decode()
        self.assertNotIn(patient.email, content)
        self.assertNotIn(patient.contact, content)

    def test_session_security(self):
        """Test que les sessions sont sécurisées."""
        # Login
        self.client.login(username='admin', password='admin123!')

        # Check session cookie settings
        session_cookie = None
        for cookie in self.client.cookies:
            if cookie == 'sessionid':
                session_cookie = self.client.cookies[cookie]
                break

        self.assertIsNotNone(session_cookie)
        # Should be httpOnly (can't be accessed by JavaScript)
        self.assertTrue(session_cookie.get('httponly', False))

    def test_password_validation(self):
        """Test que la validation des mots de passe fonctionne."""
        weak_passwords = [
            '123456',
            'password',
            'admin',
            'qwerty',
        ]

        for password in weak_passwords:
            with self.subTest(password=password):
                # Try to create user with weak password
                response = self.client.post(
                    reverse('register'),
                    {
                        'username': f'user{len(weak_passwords)}',
                        'email': f'user{len(weak_passwords)}@example.com',
                        'password1': password,
                        'password2': password,
                        'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '').value
                    }
                )

                # Should fail validation
                if response.status_code == 200:  # Form rendered with errors
                    self.assertContains(response, 'password')

    def test_file_upload_security(self):
        """Test que l'upload de fichiers est sécurisé."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Create malicious file
        malicious_file = SimpleUploadedFile(
            "evil.php",
            b'<?php echo "Malicious code"; ?>',
            content_type="application/x-php"
        )

        self.client.login(username='admin', password='admin123!')

        # Try to upload
        response = self.client.post(
            reverse('upload_document'),
            {
                'file': malicious_file,
                'csrfmiddlewaretoken': self.client.cookies.get('csrftoken', '').value
            }
        )

        # Should be rejected
        self.assertNotEqual(response.status_code, 200)

    def test_api_authentication(self):
        """Test que l'API nécessite une authentification."""
        # Try to access API without auth
        response = self.client.get('/api/patients/')

        # Should require authentication
        self.assertEqual(response.status_code, 401)