from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Основное приложение'

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'
    verbose_name = 'Основное приложение'

    def ready(self):
        """Создает игровые системы при первом запуске"""
        from django.db.models.signals import post_migrate
        from .models import GameSystem

        def create_default_systems(sender, **kwargs):
            if not GameSystem.objects.exists():
                GameSystem.create_default_systems()

        post_migrate.connect(create_default_systems, sender=self)