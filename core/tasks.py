from __future__ import absolute_import, unicode_literals
from celery import shared_task
import logging
import os
import django

logger = logging.getLogger(__name__)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()


@shared_task
def test_task():
    logger.info("Test task executed")
    return "Test task executed"
