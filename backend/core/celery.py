# ============================================
# While Health - Configuration Celery
# ============================================

import os
from celery import Celery
from celery.schedules import crontab

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('while_health')

# Utiliser les settings Django pour la config
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-découverte des tâches
app.autodiscover_tasks()

# Configuration des tâches planifiées
app.conf.beat_schedule = {
    'generate-monthly-stats': {
        'task': 'core.tasks.generate_monthly_statistics',
        'schedule': crontab(day_of_month=1, hour=9),  # 1er du mois à 9h
    },
    'cleanup-old-reports': {
        'task': 'core.tasks.cleanup_old_reports',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
    },
}

# Optimisations de performance
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
app.conf.worker_disable_rate_limits = False

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')