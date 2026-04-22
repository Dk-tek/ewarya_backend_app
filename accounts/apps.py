from django.apps import AppConfig
from django.db.backends.signals import connection_created


def configure_sqlite_connection(sender, connection, **kwargs):
    if connection.vendor != 'sqlite':
        return

    with connection.cursor() as cursor:
        cursor.execute('PRAGMA journal_mode=MEMORY;')
        cursor.execute('PRAGMA temp_store=MEMORY;')


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        connection_created.connect(configure_sqlite_connection)
