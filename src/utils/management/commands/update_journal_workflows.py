from django.core.management.base import BaseCommand

from journal import models as jm
from core import models as cm


class Command(BaseCommand):
    help = 'Loops through all journals adding the Typesetting plugin' \
           ' to workflows'

    def handle(self, *args, **options):
        try:
            from plugins.typesetting import plugin_settings
        except ImportError:
            exit("The typesetting plugin could not be imported.")

        journals = jm.Journal.objects.all()

        for journal in journals:
            workflow = cm.Workflow.objects.get(
                journal=journal
            )
            elements_to_remove = ['production', 'proofing']

            cm.WorkflowElement.objects.filter(
                journal=journal,
                element_name__in=elements_to_remove,
            ).delete()

            ts_element, c = cm.WorkflowElement.objects.get_or_create(
                journal=journal,
                element_name=plugin_settings.PLUGIN_NAME,
                defaults={
                    'handshake_url': plugin_settings.HANDSHAKE_URL,
                    'jump_url': plugin_settings.JUMP_URL,
                    'stage': plugin_settings.STAGE,
                }
            )
            workflow.elements.add(ts_element)

            stage_order = [
                'review',
                'copyediting',
                'Typesetting Plugin',
                'prepublication',
            ]

            journal_elements = cm.WorkflowElement.objects.filter(
                journal=journal,
            )
            print(journal_elements)

            for element in journal_elements:
                order = stage_order.index(element.element_name)
                element.order = order
                element.save()
