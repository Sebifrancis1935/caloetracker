from django.apps import AppConfig

class CaloeConfig(AppConfig):  # Changed from TrackerConfig to CaloeConfig
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'caloe'  # Updated to 'caloe'

    def ready(self):
        # Import signals only after app is fully loaded
        try:
            import caloe.signals  # Updated to 'caloe'
        except ImportError:
            pass