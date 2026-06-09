from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        try:
            from django.core.management import call_command
            call_command('migrate', interactive=False)
            print("[AppInit Migration] Migrations executed successfully on startup!")
        except Exception as e:
            print(f"[AppInit Migration Error] {e}")
