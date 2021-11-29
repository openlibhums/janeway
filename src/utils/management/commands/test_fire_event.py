import json
import os
from mock import Mock

from django.core.management.base import BaseCommand
from django.apps import apps
from django.http import HttpRequest

from events import logic as event_logic
from journal import models
from core import models as core_models


def create_fake_request(journal, user):
    request = Mock(HttpRequest)
    request.GET = Mock()
    request.journal = journal
    request.user = user
    request.site_type = journal
    request.FILES = None
    request.META = {}
    request.press = journal.press
    request.META = {'REMOTE_ADDR': '127.0.0.1'}
    request.model_content_type = None

    return request


class Command(BaseCommand):
    help = "Test fires an event so you can see the output."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('journal_code')
        parser.add_argument('user_id')
        parser.add_argument('event_name')
        parser.add_argument('json_path')

    def handle(self, *args, **options):
        journal_code = options.get('journal_code')
        user_id = options.get('user_id')
        event_name = options.get('event_name')
        json_path = options.get('json_path')

        user = core_models.Account.objects.get(pk=user_id)
        journal = models.Journal.objects.get(code=journal_code)
        request = create_fake_request(journal, user)

        context = {
            'request': request,
        }

        if not os.path.isfile(json_path):
            exit('File does not exist.')

        file = open(json_path, 'r')
        json_string = file.read()
        json_dict = json.loads(json_string)

        for row in json_dict:
            row_type = row.get('type')
            context_name = row.get('context_name')

            if row_type == 'model':
                app = row.get('app')
                model = row.get('model')
                pk = row.get('pk')
                Model = apps.get_model(app, model)
                obj = Model.objects.get(pk=pk)
                context[context_name] = obj

            elif row_type == 'variable':
                var = row.get('var')
                context[context_name] = var

        event_logic.Events.raise_event(
            event_name,
            **context,
        )

