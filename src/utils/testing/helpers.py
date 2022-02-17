__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from contextlib import ContextDecorator
import sys

from django.core.management import call_command
from django.utils import translation, timezone
from django.utils.six import StringIO

from core import (
    middleware,
    models as core_models,
    files,
)
from journal import models as journal_models
from press import models as press_models
from submission import models as sm_models
from utils.install import update_xsl_files, update_settings, update_issue_types
from repository import models as repo_models


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
    user = core_models.Account.objects.create_user(email=username, **kwargs)

    for role in roles:
        try:
            resolved_role = core_models.Role.objects.get(name=role)
        except core_models.Role.DoesNotExist:
            create_roles(roles)
            resolved_role = core_models.Role.objects.get(name=role)
        core_models.AccountRole(user=user, role=resolved_role, journal=journal).save()

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
        core_models.Role(name=role, slug=role).save()


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

    return journal_one, journal_two


def create_press():
    return press_models.Press.objects.create(name='Press', domain='localhost', main_contact='a@b.com')

def create_issue(journal, vol=0, number=0, articles=None):
    issue = journal_models.Issue.objects.create(
        journal=journal,
        issue=number,
        volume=vol,
        issue_type=journal_models.IssueType.objects.get(code="issue"),
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


def create_editor(journal):
    editor = create_user("editoruser@martineve.com", ["editor"], journal=journal)
    editor.is_active = True
    editor.save()
    return editor


def create_author(journal):
    attrs = {
        "first_name": "Author",
        "middle_name": "A",
        "last_name": "User",
        "institution": "Author institution",
        "department": "Author Department",
        "biography": "Author test biography"
    }
    author = create_user(
        "authoruser@martineve.com", ["author"],
        journal=journal,
        **attrs,
    )
    author.is_active = True
    author.save()
    return author


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


def create_repository(press, managers, subject_editors):
    repository, c = repo_models.Repository.objects.get_or_create(
        press=press,
        name='Test Repository',
        short_name='testrepo',
        object_name='Preprint',
        object_name_plural='Preprints',
        publisher='Test Publisher',
        live=True,
    )
    repository.managers.add(*managers)

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


def create_preprint(repository, author, subject):
    preprint = repo_models.Preprint.objects.create(
        repository=repository,
        owner=author,
        stage=repo_models.STAGE_PREPRINT_REVIEW,
        title='This is a Test Preprint',
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
    repo_models.PreprintAuthor.objects.create(
        preprint=preprint,
        account=author,
        order=1,
        affiliation='Made Up University',
    )
    return preprint


class Request(object):
    """
    A fake request class for sending emails outside of the
    client-server request loop.
    """

    def __init__(self):
        self.journal = None
        self.site_type = None
        self.port = 8000
        self.secure = False
        self.user = False
        self.FILES = None
        self.META = {'REMOTE_ADDR': '127.0.0.1'}
        self.model_content_type = None

    def is_secure(self):
        if self.secure is False:
            return False
        else:
            return True

    def get_host(self):
        return 'testserver'


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
