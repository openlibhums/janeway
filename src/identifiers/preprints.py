import requests
from uuid import uuid4
from datetime import datetime
from crossref.restful import Depositor

from django.template.loader import render_to_string

from identifiers import models, logic
from utils.logger import get_logger
from utils import models as util_models

logger = get_logger(__name__)


def check_repository_crossref_settings(repository):
    settings = [
        repository.crossref_username,
        repository.crossref_password,
        repository.crossref_depositor_name,
        repository.crossref_depositor_email,
        repository.crossref_registrant,
        repository.crossref_prefix,
    ]
    if any(settings) is None:
        return False, 'Some crossref settings are missing.'
    return True, ''


def get_dois_for_preprint_versions(preprint_versions):
    identifiers = []
    for preprint_version in preprint_versions:
        identifier, c = models.Identifier.objects.get_or_create(
            id_type='doi',
            preprint_version=preprint_version,
            defaults={
                'identifier': preprint_version.get_doi_pattern(),
            }
        )
        identifiers.append(identifier)
    return identifiers


def send_preprint_version_crossref_deposit(repository, versions, identifiers):
    identifiers = set((i for i in identifiers))
    template = 'common/identifiers/crossref_preprint_batch.xml'
    template_context = {
        'versions': versions,
        'batch_id': uuid4(),
        'repository': repository,
        'now': datetime.now(),
    }
    document = render_to_string(
        template,
        template_context,
    )
    filename = uuid4()
    crossref_deposit = models.CrossrefDeposit.objects.create(
        document=document,
        file_name=filename,
    )
    for identifier in identifiers:
        crossref_status, c = models.CrossrefStatus.objects.get_or_create(
            identifier=identifier,
        )
        crossref_status.deposits.add(crossref_deposit)
    depositor = Depositor(
        prefix=repository.crossref_prefix,
        api_user=repository.crossref_username,
        api_key=repository.crossref_password,
        use_test_server=repository.crossref_test_mode,
    )
    try:
        response = depositor.register_doi(
            submission_id=filename,
            request_xml=crossref_deposit.document,
        )
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        status = 'Error depositing. Could not connect to Crossref ({0}). Error: {1}'.format(
            depositor.get_endpoint(verb='deposit'),
            e,
        )
        crossref_deposit.result_text = status
        crossref_deposit.save()
        logger.error(status)
        return status, e
    if response.status_code == 200:
        status = f"Deposit sent ({repository.short_name})"
        util_models.LogEntry.bulk_add_simple_entry(
            'Submission',
            status,
            'Info',
            targets=versions,
        )
        logger.info(status)
    for identifier in identifiers:
        crossref_status = models.CrossrefStatus.objects.get(
            identifier=identifier,
        )
        crossref_status.update()


def deposit_doi_for_preprint_version(repository, preprint_versions):
    if repository.crossref_enable:
        status, error = check_repository_crossref_settings(repository)

        if not error:
            identifiers = get_dois_for_preprint_versions(preprint_versions)
            return send_preprint_version_crossref_deposit(
                repository,
                preprint_versions,
                identifiers
            )
