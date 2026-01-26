# converter/apps.py
from django.apps import AppConfig

class ConverterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'converter'

    def ready(self):
        try:
            import converter.signals
            print("[INFO] Signals de converter importados com sucesso")
        except Exception as e:
            print(f"[ERRO] Falha ao importar signals: {e}")