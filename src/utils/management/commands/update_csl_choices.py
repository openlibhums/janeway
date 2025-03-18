import os
from xml.etree import ElementTree as ET

from django.core.management.base import BaseCommand

from utils.logger import get_logger

from submission.models import CitationStyleLanguage

logger = get_logger(__name__)


class Command(BaseCommand):
    help = 'Updates the citation style choices in Janeway from the CSL GH repo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=0,
        )
        parser.add_argument(
            'csl_repo_path',
            type=str,
            help='Local clone location of https://github.com/citation-style-language/styles',
        )

    def handle(self, *args, **options):

        ET.register_namespace('csl', 'http://purl.org/net/xbiblio/csl')
        csl_repo_path = options['csl_repo_path']
        xpath_prefix = './/{http://purl.org/net/xbiblio/csl}'
        with os.scandir(csl_repo_path) as entries:
            i = 0
            objects_to_create = []
            current_objects_by_csl_id = {
                obj.csl_id: obj for obj in CitationStyleLanguage.objects.all()
            }
            for entry in entries:
                i += 1
                if i == options['limit']:
                    return
                if entry.name.endswith('.csl') and entry.is_file():
                    full_path = os.path.join(csl_repo_path, entry.name)
                    normalized_name = entry.name[:-4]
                    tree = ET.parse(full_path)
                    title_element = tree.find(xpath_prefix + 'title')
                    try:
                        display_name = title_element.text
                    except AttributeError:
                        display_name = ''
                    id_element = tree.find(xpath_prefix + 'id')
                    try:
                        csl_id = id_element.text
                    except AttributeError:
                        csl_id = ''
                    if csl_id in current_objects_by_csl_id:
                        return
                    objects_to_create.append(
                        CitationStyleLanguage(
                            normalized_name=normalized_name,
                            display_name=display_name,
                            csl_id=csl_id,
                        )
                    )
            CitationStyleLanguage.objects.bulk_create(objects_to_create)


        logger.debug(
            self.style.SUCCESS(
                f'Successfully updated citation style choices'
            )
        )
