__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os
from contextlib import ContextDecorator
from unittest.mock import Mock
import datetime

from django.http import HttpRequest
from django.test.client import QueryDict
from django.utils import translation, timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from utils import template_override_middleware
from django.template.engine import Engine

from core import (
    middleware,
    models as core_models,
    files,
)
from core.models import File
from journal import models as journal_models
from press import models as press_models
from submission import models as sm_models
from review import models as review_models
from copyediting import models as copyediting_models
from comms import models as comms_models
from cms import models as cms_models
from utils import setting_handler
from utils.install import update_xsl_files, update_settings, update_issue_types
from repository import models as repo_models
from utils.logic import get_aware_datetime
from uuid import uuid4
from review.const import ReviewerDecisions as RD
from cms import models as cms_models


def create_user(username, roles=None, journal=None, **attrs):
    """
    Creates a user with the specified permissions.
    :username: A unique username to set the user username and email
    :roles: A list[str] of roles to be granted to the user
    :journal: The Journal object to which the above roles will be linked
    :attrs: key/value pairs of further attributes to set on the user object
    :return: a user with the specified permissions
    """
    # check this way to avoid mutable default argument
    if roles is None:
        roles = []

    kwargs = {'username': username}
    try:
        user = core_models.Account.objects.get(email=username)
    except core_models.Account.DoesNotExist:
        user = core_models.Account.objects.create_user(email=username, **kwargs)

    for role in roles:
        try:
            resolved_role = core_models.Role.objects.get(slug=role)
        except core_models.Role.DoesNotExist:
            create_roles(roles)
            resolved_role = core_models.Role.objects.get(slug=role)
        core_models.AccountRole.objects.get_or_create(
            user=user,
            role=resolved_role,
            journal=journal
        )

    for attr, value in attrs.items():
        setattr(user, attr, value)

    user.save()

    return user


def create_roles(roles=None):
    """
    Creates the necessary roles for testing.
    :return: None
    """
    # check this way to avoid mutable default argument
    if roles is None:
        roles = []

    for role in roles:
        core_models.Role.objects.get_or_create(
            name=role.replace('-', ' ').capitalize(),
            slug=role.lower().replace(' ', '-')
        )


def create_journals():
    """
    Creates a set of dummy journals for testing
    :return: a 2-tuple of two journals
    """
    update_settings()
    update_xsl_files()
    journal_one = journal_models.Journal(code="TST", domain="testserver")
    journal_one.save()

    journal_two = journal_models.Journal(code="TSA", domain="journal2.localhost")
    journal_two.save()

    journal_one.name = 'Journal One'
    journal_two.name = 'Journal Two'
    update_issue_types(journal_one)
    update_issue_types(journal_two)

    return journal_one, journal_two


def create_press():
    return press_models.Press.objects.create(name='Press', domain='localhost', main_contact='a@b.com')


def create_issue(journal, vol=0, number=0, articles=None):
    issue_type, created = journal_models.IssueType.objects.get_or_create(
        code="issue",
        journal=journal,
    )
    issue_datetime = get_aware_datetime('2022-01-01')
    issue, created = journal_models.Issue.objects.get_or_create(
        journal=journal,
        issue=number,
        volume=vol,
        defaults={
            'issue_title': ('Test Issue from Utils Testing Helpers'),
            'issue_type': issue_type,
            'date': issue_datetime,
        },
    )
    if articles:
        issue.articles.add(*articles)
    return issue


def create_regular_user():
    regular_user = create_user("regularuser@martineve.com")
    regular_user.is_active = True
    regular_user.save()
    return regular_user


def create_second_user(journal):
    second_user = create_user("seconduser@martineve.com", ["reviewer"], journal=journal)
    second_user.is_active = True
    second_user.save()
    return second_user


def create_editor(journal, **kwargs):
    email = kwargs.pop("email", "editoruser@martineve.com")
    editor = create_user(email, ["editor"], journal=journal)
    editor.is_active = True
    editor.save()
    return editor


def create_section_editor(journal, **kwargs):
    email = kwargs.pop('email', 'section_editor@example.com')
    roles = ['section-editor']
    se = create_user(email, roles=roles, journal=journal)
    se.is_active = True
    se.save()
    return se


def create_peer_reviewer(journal, **kwargs):
    email = kwargs.pop('email', 'peer_reviewer@example.com')
    roles = ['reviewer']
    reviewer = create_user(email, roles=roles, journal=journal)
    reviewer.is_active = True
    reviewer.save()
    return reviewer


def create_affiliation(
    institution='',
    department='',
    account=None,
    frozen_author=None,
    preprint_author=None,
):
    organization = core_models.Organization.objects.create()
    core_models.OrganizationName.objects.create(
        value=institution,
        custom_label_for=organization,
    )
    affiliation = core_models.ControlledAffiliation.objects.create(
        organization=organization,
        department=department,
        account=account,
        frozen_author=frozen_author,
        preprint_author=preprint_author,
    )
    return affiliation


def create_author(journal, **kwargs):
    roles = kwargs.pop('roles', ['author'])
    email = kwargs.pop('email', "authoruser@martineve.com")
    attrs = {
        "first_name": "Author",
        "middle_name": "A",
        "last_name": "User",
        "biography": "Author test biography"
    }
    attrs.update(kwargs)
    author = create_user(
        email,
        roles=roles,
        journal=journal,
        **attrs,
    )
    author.is_active = True
    author.save()
    create_affiliation(
        institution="Author institution",
        department="Author Department",
        account=author,
    )
    return author


def create_article(journal, **kwargs):

    article = sm_models.Article.objects.create(
        journal=journal,
        title='Test Article from Utils Testing Helpers',
        article_agreement='Test Article',
        section=create_section(journal),
    )

    if kwargs.pop('with_author', False):
        author_kwargs ={
            'salutation': 'Dr.',
            'name_suffix': 'Jr.',
            'orcid': '1234-5678-9012-345X',
            'email': '{}{}'.format(uuid4(), settings.DUMMY_EMAIL_DOMAIN)
        }
        author = create_author(journal, **author_kwargs)
        article.authors.add(author)
        article.owner = author
        article.save()
        author.snapshot_self(article)
    else:
        article.save()
    for k,v in kwargs.items():
        setattr(article, k ,v)
        article.save()
    return article


def create_galley(article, file_obj=None, **kwargs):
    if not file_obj:
        file_obj = File.objects.create(
            article_id=article.pk,
            label="file",
            is_galley=True,
            uuid_filename="test.txt"
        )
    galley = core_models.Galley.objects.create(
        article_id=article.pk,
        file=file_obj,
        **kwargs,
    )
    article.galley_set.add(galley)
    return galley


def create_section(journal, **kwargs):
    defaults = {
        'number_of_reviewers': 2,
        'name': 'Article',
        'plural': 'Articles',
    }
    defaults.update(kwargs)

    section, created = sm_models.Section.objects.get_or_create(
        journal=journal,
        **defaults,
    )
    return section


def create_submission(
    owner=None,
    title='A Test Article',
    abstract='A Test article abstract',
    journal_id=1,
    stage=sm_models.STAGE_UNASSIGNED,
    authors=None,
    **kwargs,
):

    section, _ = sm_models.Section.objects.get_or_create(
        journal__id=journal_id, name="Article",
    )
    article = sm_models.Article.objects.create(
        owner=owner,
        title=title,
        abstract=abstract,
        journal_id=journal_id,
        stage=stage,
        section=section,
        **kwargs
    )
    if authors:
        article.authors.add(*authors)
        article.snapshot_authors()
    return article


def create_test_file(test_case, file):
    label = 'Test File'
    path_parts = ('articles', test_case.article_in_production.pk)

    file = files.save_file(
        test_case.request,
        file,
        label=label,
        public=True,
        path_parts=path_parts,
    )

    test_case.files.append(file)

    return file, path_parts


def create_repository(press, managers, subject_editors, domain='repo.domain.com'):
    repository, c = repo_models.Repository.objects.get_or_create(
        press=press,
        name='Test Repository',
        short_name='testrepo',
        object_name='Preprint',
        object_name_plural='Preprints',
        publisher='Test Publisher',
        live=True,
        domain=domain,
    )
    repository.managers.add(*managers)
    repository.save()

    subject, c = repo_models.Subject.objects.get_or_create(
        repository=repository,
        name='Repo Subject',
        slug='repo-subject',
        enabled=True,
    )
    subject.editors.add(
        *subject_editors,
    )

    return repository, subject


def create_preprint(repository, author, subject, title='This is a Test Preprint'):
    preprint = repo_models.Preprint.objects.create(
        repository=repository,
        owner=author,
        stage=repo_models.STAGE_PREPRINT_REVIEW,
        title=title,
        abstract='This is a fake abstract.',
        comments_editor='',
        date_submitted=timezone.now(),
    )
    preprint.subject.add(
        subject,
    )
    file = repo_models.PreprintFile.objects.create(
        preprint=preprint,
        original_filename='fake_file.pdf',
        mime_type='application/pdf',
        size=100,
    )
    preprint.submission_file = file
    preprint_author = repo_models.PreprintAuthor.objects.create(
        preprint=preprint,
        account=author,
        order=1,
    )
    preprint_author.save()
    create_affiliation(
        institution="Made Up University",
        preprint_author=preprint_author,
    )
    return preprint


class Request(HttpRequest):
    """
    A fake request class for running tests outside of the
    client-server request loop.
    """

    def __init__(self, **kwargs):
        super().__init__()
        self.press = kwargs.get('press', None)
        self.repository = kwargs.get('repository', None)
        self.journal = kwargs.get('journal', None)
        self.site_type = kwargs.get('site_type', None)
        self.port = kwargs.get('port', 8000)
        self.secure = kwargs.get('secure', False)
        self.user = kwargs.get('user', None)
        self.FILES = kwargs.get('FILES', None)
        self.META = kwargs.get(
            'META',
            {'REMOTE_ADDR': '127.0.0.1'}
        )
        self.GET = QueryDict()
        self.POST = QueryDict()
        self.model_content_type = kwargs.get('model_content_type', None)

    def is_secure(self):
        if self.secure is False:
            return False
        else:
            return True

    def get_host(self):
        return 'testserver'


def get_request(**kwargs):
    journal = kwargs.get('journal', None)
    press = kwargs.get('press', None)
    if journal:
        journal_type = ContentType.objects.get_for_model(journal)
        kwargs['model_content_type'] = journal_type
        kwargs['site_type'] = journal
    elif press:
        press_type = ContentType.objects.get_for_model(press)
        kwargs['model_content_type'] = press_type
        kwargs['site_type'] = press
    request = Request(**kwargs)
    return request


class activate_translation(ContextDecorator):
    def __init__(self, language_code, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.language_code = language_code

    def __enter__(self):
        translation.activate(self.language_code)

    def __exit__(self, *exc):
        translation.deactivate()


class request_context(ContextDecorator):

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request

    def __enter__(self):
        middleware._threadlocal.request = self.request

    def __exit__(self, *exc):
        middleware._threadlocal.request = None


def create_review_form(journal):
    return review_models.ReviewForm.objects.create(
        name="A Form",
        intro="i",
        thanks="t",
        journal=journal
    )


def create_round(article, round_number=1):
    return review_models.ReviewRound.objects.create(
        article=article,
        round_number=round_number,
    )


def create_review_assignment(
        journal=None,
        article=None,
        reviewer=None,
        editor=None,
        due_date=None,
        review_form=None,
        decision=None,
        is_complete=False,
        review_round=None,
        review_file=None,
    ):
    if not journal:
        journal, _journal_two = create_journals()
    if not article:
        article = create_submission(
            owner=create_regular_user(),
            journal_id=journal.pk,
            stage=sm_models.STAGE_UNDER_REVIEW
        )
    if not reviewer:
        reviewer = create_second_user(journal)
    if not editor:
        editor = create_editor(journal)
    if not due_date:
        due_date = timezone.now() + datetime.timedelta(days=3)
    if not review_form:
        review_form = create_review_form(journal)
    if not decision:
        decision = RD.DECISION_ACCEPT.value
    if not review_round:
        review_round = create_round(article)

    return review_models.ReviewAssignment.objects.create(
        article=article,
        reviewer=reviewer,
        editor=editor,
        date_due=due_date,
        form=review_form,
        decision=decision,
        is_complete=is_complete,
        date_complete=timezone.now() if is_complete else None,
        review_round=review_round,
        access_code=uuid4(),
        review_file=review_file if review_file else None,
    )


def create_reminder(journal=None, reminder_type=None):
    from cron.models import Reminder
    if not journal:
        journal, _journal_two = create_journals()
    if not reminder_type:
        reminder_type='review'
    reminder = Reminder.objects.create(
        journal=journal,
        type='review',
        run_type='before',
        days=3,
        template_name='test_reminder_'+reminder_type,
        subject='Test reminder subject',
    )

    from utils import setting_handler
    setting_handler.create_setting(
        'email',
        reminder.template_name,
        'rich-text',
        reminder.subject,
        '',
        is_translatable=True
    )
    setting_handler.save_setting(
        'email',
        reminder.template_name,
        journal,
        'Test body'
    )

    return reminder


def create_editor_assignment(article, editor, **kwargs):
    assignment_type = kwargs.get('assignment_type','editor')
    assignment, created = review_models.EditorAssignment.objects.get_or_create(
        article=article,
        editor=editor,
        editor_type=assignment_type,
    )
    return assignment


def create_revision_request(article, editor, **kwargs):
    note = kwargs.get('note', 'Test note')
    decision = kwargs.get('decision', review_models.review_decision()[0][0])
    if isinstance(decision, tuple):
        decision = decision[0]
    date_due = kwargs.get('date_due', timezone.now() + datetime.timedelta(days=3))
    revision = review_models.RevisionRequest.objects.create(
        article=article,
        editor=editor,
        editor_note=note,
        type=decision,
        date_due=date_due,
    )
    return revision


def create_copyeditor(journal, **kwargs):
    username = kwargs.pop('username', 'copyeditor@example.com')
    roles = kwargs.pop('roles', ['copyeditor'])
    return create_user(username, roles=roles, journal=journal, **kwargs)


def create_copyedit_assignment(article, copyeditor, **kwargs):
    editor = kwargs.get('editor', None)
    assigned = kwargs.get('assigned', timezone.now() - datetime.timedelta(minutes=3))
    notified = kwargs.get('notified', False)
    decision = kwargs.get('decision', False)
    date_decided = kwargs.get('date_decided', None)
    copyeditor_completed = kwargs.get('copyeditor_completed', None)
    copyedit_accepted = kwargs.get('copyedit_accepted', None)

    assignment = copyediting_models.CopyeditAssignment.objects.create(
        article=article,
        copyeditor=copyeditor,
        editor=editor,
        assigned=assigned,
        notified=notified,
        decision=decision,
        date_decided=date_decided,
        copyeditor_completed=copyeditor_completed,
        copyedit_accepted=copyedit_accepted,
    )
    return assignment


def create_access_request(journal, user, role, **kwargs):
    role = core_models.Role.objects.get(slug=role)
    access_request, created = core_models.AccessRequest.objects.get_or_create(
        journal=journal,
        user=user,
        role=role,
        text='Automatic request as author added to an article.',
    )
    return access_request


def create_news_item(content_type, object_id, **kwargs):
    title = kwargs.get('title', 'Test title')
    body = kwargs.get('body', 'Test body')
    posted_by = kwargs.get(
        'posted_by',
        create_user(
            'news_author@example.org',
            attrs={'first_name': 'News', 'last_name': 'Writer'}
        )
    )
    tags = kwargs.get('tags', ['test tag 1', 'test tag 2'])
    item = comms_models.NewsItem.objects.create(
        content_type=content_type,
        object_id=object_id,
        title=title,
        body=body,
        posted_by=posted_by,
    )
    for tag in tags:
        item.tags.add(comms_models.Tag.objects.create(text=tag))
    item.save()
    return item


def create_cms_page(content_type, object_id, **kwargs):
    name = kwargs.get('name', 'test-name')
    display_name = kwargs.get('display_name', 'Test display name')
    content = kwargs.get('content', 'Test content')
    is_markdown = kwargs.get('is_markdown', False)

    return cms_models.Page.objects.create(
        content_type=content_type,
        object_id=object_id,
        name=name,
        display_name=display_name,
        content=content,
        is_markdown=is_markdown,
    )


def create_contact(content_type, object_id, **kwargs):
    name = kwargs.get('name', 'Test Contact')
    email = kwargs.get('email', 'contact@example.org')
    role = kwargs.get('role', 'Test contact role')
    return core_models.Contacts.objects.create(
        content_type=content_type,
        object_id=object_id,
        name=name,
        email=email,
        role=role,
    )

def create_setting(
        setting_group_name='test_group',
        setting_name='test_setting',
        setting_type='rich-text',
        pretty_name='Test Setting',
        description='A test setting.',
        is_translatable=True,
        default_value='Default setting value',
    ):
    return setting_handler.create_setting(
        setting_group_name,
        setting_name,
        setting_type,
        pretty_name,
        description,
        is_translatable=is_translatable,
        default_value=default_value,
    )

def get_orcid_record_all_fields():
    return {'orcid-identifier': {'uri': 'http://sandbox.orcid.org/0000-0000-0000-0000', 'path': '0000-0000-0000-0000', 'host': 'sandbox.orcid.org'}, 'preferences': {'locale': 'EN'}, 'history': {'creation-method': 'DIRECT', 'completion-date': None, 'submission-date': {'value': 1716899022299}, 'last-modified-date': {'value': 1717012729950}, 'claimed': True, 'source': None, 'deactivation-date': None, 'verified-email': True, 'verified-primary-email': True}, 'person': {'last-modified-date': {'value': 1717012710380}, 'name': {'created-date': {'value': 1716899022606}, 'last-modified-date': {'value': 1716931428927}, 'given-names': {'value': 'cdleschol'}, 'family-name': {'value': 'arship'}, 'credit-name': None, 'source': None, 'visibility': 'PUBLIC', 'path': '0000-0000-0000-0000'}, 'other-names': {'last-modified-date': None, 'other-name': [], 'path': '/0000-0000-0000-0000/other-names'}, 'biography': None, 'researcher-urls': {'last-modified-date': None, 'researcher-url': [], 'path': '/0000-0000-0000-0000/researcher-urls'}, 'emails': {'last-modified-date': {'value': 1717012710380}, 'email': [{'created-date': {'value': 1716899022599}, 'last-modified-date': {'value': 1717012710380}, 'source': {'source-orcid': {'uri': 'http://sandbox.orcid.org/0000-0000-0000-0000', 'path': '0000-0000-0000-0000', 'host': 'sandbox.orcid.org'}, 'source-client-id': None, 'source-name': {'value': 'cdleschol arship'}}, 'email': 'cdleschol@mailinator.com', 'path': None, 'visibility': 'PUBLIC', 'verified': True, 'primary': True, 'put-code': None}], 'path': '/0000-0000-0000-0000/email'}, 'addresses': {'last-modified-date': {'value': 1716931402191}, 'address': [{'created-date': {'value': 1716931402191}, 'last-modified-date': {'value': 1716931402191}, 'source': {'source-orcid': {'uri': 'http://sandbox.orcid.org/0000-0000-0000-0000', 'path': '0000-0000-0000-0000', 'host': 'sandbox.orcid.org'}, 'source-client-id': None, 'source-name': {'value': 'cdleschol arship'}}, 'country': {'value': 'US'}, 'visibility': 'PUBLIC', 'path': '/0000-0000-0000-0000/address/7884', 'put-code': 7884, 'display-index': 1}], 'path': '/0000-0000-0000-0000/address'}, 'keywords': {'last-modified-date': None, 'keyword': [], 'path': '/0000-0000-0000-0000/keywords'}, 'external-identifiers': {'last-modified-date': None, 'external-identifier': [], 'path': '/0000-0000-0000-0000/external-identifiers'}, 'path': '/0000-0000-0000-0000/person'}, 'activities-summary': {'last-modified-date': {'value': 1716931455651}, 'educations': {'last-modified-date': None, 'education-summary': [], 'path': '/0000-0000-0000-0000/educations'}, 'employments': {'last-modified-date': {'value': 1716931455651}, 'employment-summary': [{'created-date': {'value': 1716931455651}, 'last-modified-date': {'value': 1716931455651}, 'source': {'source-orcid': {'uri': 'http://sandbox.orcid.org/0000-0000-0000-0000', 'path': '0000-0000-0000-0000', 'host': 'sandbox.orcid.org'}, 'source-client-id': None, 'source-name': {'value': 'cdleschol arship'}}, 'department-name': None, 'role-title': None, 'start-date': None, 'end-date': None, 'organization': {'name': 'California Digital Library', 'address': {'city': 'Oakland', 'region': 'California', 'country': 'US'}, 'disambiguated-organization': {'disambiguated-organization-identifier': 'https://ror.org/03yrm5c26', 'disambiguation-source': 'ROR'}}, 'visibility': 'PUBLIC', 'put-code': 66225, 'path': '/0000-0000-0000-0000/employment/66225'}], 'path': '/0000-0000-0000-0000/employments'}, 'fundings': {'last-modified-date': None, 'group': [], 'path': '/0000-0000-0000-0000/fundings'}, 'peer-reviews': {'last-modified-date': None, 'group': [], 'path': '/0000-0000-0000-0000/peer-reviews'}, 'works': {'last-modified-date': None, 'group': [], 'path': '/0000-0000-0000-0000/works'}, 'path': '/0000-0000-0000-0000/activities'}, 'path': '/0000-0000-0000-0000'}

def get_orcid_record_min_fields():
    return {'orcid-identifier': {'uri': 'http://sandbox.orcid.org/0000-0000-0000-0000', 'path': '0000-0000-0000-0000', 'host': 'sandbox.orcid.org'}, 'preferences': {'locale': 'EN'}, 'history': {'creation-method': 'DIRECT', 'completion-date': None, 'submission-date': {'value': 1716899022299}, 'last-modified-date': {'value': 1717012843372}, 'claimed': True, 'source': None, 'deactivation-date': None, 'verified-email': True, 'verified-primary-email': True}, 'person': {'last-modified-date': None, 'name': None, 'other-names': {'last-modified-date': None, 'other-name': [], 'path': '/0000-0000-0000-0000/other-names'}, 'biography': None, 'researcher-urls': {'last-modified-date': None, 'researcher-url': [], 'path': '/0000-0000-0000-0000/researcher-urls'}, 'emails': {'last-modified-date': None, 'email': [], 'path': '/0000-0000-0000-0000/email'}, 'addresses': {'last-modified-date': None, 'address': [], 'path': '/0000-0000-0000-0000/address'}, 'keywords': {'last-modified-date': None, 'keyword': [], 'path': '/0000-0000-0000-0000/keywords'}, 'external-identifiers': {'last-modified-date': None, 'external-identifier': [], 'path': '/0000-0000-0000-0000/external-identifiers'}, 'path': '/0000-0000-0000-0000/person'}, 'activities-summary': {'last-modified-date': None, 'educations': {'last-modified-date': None, 'education-summary': [], 'path': '/0000-0000-0000-0000/educations'}, 'employments': {'last-modified-date': None, 'employment-summary': [], 'path': '/0000-0000-0000-0000/employments'}, 'fundings': {'last-modified-date': None, 'group': [], 'path': '/0000-0000-0000-0000/fundings'}, 'peer-reviews': {'last-modified-date': None, 'group': [], 'path': '/0000-0000-0000-0000/peer-reviews'}, 'works': {'last-modified-date': None, 'group': [], 'path': '/0000-0000-0000-0000/works'}, 'path': '/0000-0000-0000-0000/activities'}, 'path': '/0000-0000-0000-0000'}

def get_ror_records():
    return [{"admin":{"created":{"date":"2018-11-14","schema_version":"1.0"},"last_modified":{"date":"2024-12-11","schema_version":"2.1"}},"domains":["kea.dk"],"established":2009,"external_ids":[{"all":["grid.466211.6"],"preferred":"grid.466211.6","type":"grid"},{"all":["0000 0004 0469 3633"],"preferred":None,"type":"isni"},{"all":["Q25044653"],"preferred":None,"type":"wikidata"}],"id":"https://ror.org/00j1xwp39","links":[{"type":"website","value":"https://kea.dk"},{"type":"wikipedia","value":"https://en.wikipedia.org/wiki/KEA_%E2%80%93_Copenhagen_School_of_Design_and_Technology"}],"locations":[{"geonames_details":{"continent_code":"EU","continent_name":"Europe","country_code":"DK","country_name":"Denmark","country_subdivision_code":"84","country_subdivision_name":"Capital Region","lat":55.67594,"lng":12.56553,"name":"Copenhagen"},"geonames_id":2618425}],"names":[{"lang":"en","types":["ror_display","label"],"value":"Copenhagen School of Design and Technology"},{"lang":None,"types":["acronym"],"value":"KEA"},{"lang":"da","types":["label"],"value":"K\u00f8benhavns Erhvervsakademi"}],"relationships":[],"status":"active","types":["education"]},{"admin":{"created":{"date":"2018-11-14","schema_version":"1.0"},"last_modified":{"date":"2024-12-11","schema_version":"2.1"}},"domains":["kfe.re.kr"],"established":1995,"external_ids":[{"all":["501100003721"],"preferred":None,"type":"fundref"},{"all":["grid.419380.7"],"preferred":"grid.419380.7","type":"grid"}],"id":"https://ror.org/013yz9b19","links":[{"type":"website","value":"https://www.kfe.re.kr/"}],"locations":[{"geonames_details":{"continent_code":"AS","continent_name":"Asia","country_code":"KR","country_name":"South Korea","country_subdivision_code":"30","country_subdivision_name":"Daejeon","lat":36.34913,"lng":127.38493,"name":"Daejeon"},"geonames_id":1835235}],"names":[{"lang":None,"types":["acronym"],"value":"KFE"},{"lang":"en","types":["ror_display","label"],"value":"Korea Institute of Fusion Energy"}],"relationships":[],"status":"active","types":["facility","funder"]},{"admin":{"created":{"date":"2018-11-14","schema_version":"1.0"},"last_modified":{"date":"2024-12-11","schema_version":"2.1"}},"domains":["turing.ac.uk"],"established":2015,"external_ids":[{"all":["100012338"],"preferred":"100012338","type":"fundref"},{"all":["grid.499548.d"],"preferred":"grid.499548.d","type":"grid"},{"all":["0000 0004 5903 3632"],"preferred":None,"type":"isni"},{"all":["Q16826821"],"preferred":None,"type":"wikidata"}],"id":"https://ror.org/035dkdb55","links":[{"type":"website","value":"https://www.turing.ac.uk"},{"type":"wikipedia","value":"https://en.wikipedia.org/wiki/Alan_Turing_Institute"}],"locations":[{"geonames_details":{"continent_code":"EU","continent_name":"Europe","country_code":"GB","country_name":"United Kingdom","country_subdivision_code":"ENG","country_subdivision_name":"England","lat":51.50853,"lng":-0.12574,"name":"London"},"geonames_id":2643743}],"names":[{"lang":"en","types":["ror_display","label"],"value":"The Alan Turing Institute"}],"relationships":[],"status":"active","types":["facility","funder"]}]
