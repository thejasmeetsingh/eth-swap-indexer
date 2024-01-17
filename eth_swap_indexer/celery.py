import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eth_swap_indexer.settings')

app = Celery('eth_swap_indexer')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(["app"])
