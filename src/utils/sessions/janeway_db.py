from datetime import timedelta

from django.contrib.sessions.backends import db
from django.utils import timezone
from django.db import transaction


class SessionStore(db.SessionStore):

    @classmethod
    @transaction.atomic
    def clear_expired(cls):
        cls.get_model_class().objects.filter(
            expire_date__lt=timezone.now()).delete()
