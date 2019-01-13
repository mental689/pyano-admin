from django.apps import AppConfig
from django.db.models.signals import post_migrate

from vatic.signals import handlers


class VaticConfig(AppConfig):
    name = 'vatic'

    def ready(self):
        post_migrate.connect(handlers.create_notice_types, sender=self)
