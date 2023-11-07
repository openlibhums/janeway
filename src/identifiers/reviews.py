import requests
from uuid import uuid4
from datetime import datetime
from crossref.restful import Depositor

from django.template.loader import render_to_string

from identifiers import models, logic
from utils.logger import get_logger
from utils import models as util_models

logger = get_logger(__name__)


def deposit_doi_for_reviews(journal, reviews):
    status, error, journals = logic.check_deposits_from_same_journal(
        [review.article for review in reviews]
    )
    if error:
        logger.debug(status)
        return status, error
    use_crossref, mode, missing_settings = logic.check_crossref_settings(
        journal
    )
    # Filter out non-accepted articles
    reviews = filter_non_accepted_articles(reviews)
    identifiers = get_dois_for_reviews(reviews)
    if use_crossref and not missing_settings:
        return send_review_crossref_deposit(
            mode,
            reviews,
            identifiers,
            journal,
        )


def get_dois_for_reviews(reviews):
    identifiers = []
    for review in reviews:
        identifier, c = models.Identifier.objects.get_or_create(
            id_type='doi',
            review=review,
            defaults={
                'identifier': review.get_doi_pattern(),
            }
        )
        identifiers.append(identifier)
    return identifiers


def filter_non_accepted_articles(reviews):
    pks_to_exclude = list()
    for review in reviews:
        if not review.article.is_accepted():
            pks_to_exclude.append(review.pk)
    return reviews.exclude(pk__in=pks_to_exclude)


def send_review_crossref_deposit(mode, reviews, identifiers, journal):
    # Form a set from the iterable passed in
    identifiers = set((i for i in identifiers))
    template = 'common/identifiers/crossref_review_batch.xml'
    template_context = {
        'reviews': reviews,
        'batch_id': uuid4(),
        'now': datetime.now(),
        'timestamp_suffix': journal.get_setting(
            'crossref',
            'crossref_date_suffix',
        ),
        'depositor_name': journal.get_setting(
            'Identifiers',
            'crossref_name',
        ),
        'depositor_email': journal.get_setting(
            'Identifiers',
            'crossref_email',
        ),
        'registrant': journal.get_setting(
            'Identifiers',
            'crossref_registrant',
        ),
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

    doi_prefix = journal.get_setting(
        'Identifiers',
        'crossref_prefix',
    )
    username = journal.get_setting(
        'Identifiers',
        'crossref_username',
    )
    password = journal.get_setting(
        'Identifiers',
        'crossref_password',
    )
    depositor = Depositor(
        prefix=doi_prefix,
        api_user=username,
        api_key=password,
        use_test_server=mode,
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
        status = f"Deposit sent ({journal.code})"
        util_models.LogEntry.bulk_add_simple_entry(
            'Submission',
            status,
            'Info',
            targets=reviews,
        )
        logger.info(status)
    for identifier in identifiers:
        crossref_status = models.CrossrefStatus.objects.get(
            identifier=identifier,
        )
        crossref_status.update()
