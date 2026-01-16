# core/celery.py

import os
from celery import Celery
from django.conf import settings

# Define o settings module padrão para o Celery (importante para rodar comandos celery)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Cria a instância do Celery com o nome do projeto
app = Celery('core')

# Carrega todas as configurações do Django que começam com CELERY_
# O namespace='CELERY' faz com que CELERY_BROKER_URL vire broker_url internamente
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-descoberta de tasks em todos os apps listados em INSTALLED_APPS
# Isso inclui o app 'services' onde está a send_email_task
app.autodiscover_tasks()

# Opcional: tarefa de debug (útil para testar se o worker está funcionando)
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')