from django.apps import AppConfig #type: ignore




class StaffConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'staff'
    
    def ready(self):
        import staff.signals  # Importez les signaux pour qu'ils soient enregistrés dans l'application
