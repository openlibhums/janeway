__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from contextlib import ContextDecorator

from django.utils import translation, timezone
from django.conf import settings
from django.utils import timezone
import datetime

from core import (
    middleware,
    models as core_models,
    files,
)
from journal import models as journal_models
from press import models as press_models
from submission import models as sm_models
from review import models as review_models
from copyediting import models as copyediting_models
from utils.install import update_xsl_files, update_settings, update_issue_types
from repository import models as repo_models
from utils.logic import get_aware_datetime
from uuid import uuid4


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


def create_author(journal, **kwargs):
    roles = kwargs.pop('roles', ['author'])
    email = kwargs.pop('email', "authoruser@martineve.com")
    attrs = {
        "first_name": "Author",
        "middle_name": "A",
        "last_name": "User",
        "institution": "Author institution",
        "department": "Author Department",
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
    return author


def create_article(journal, **kwargs):

    article = sm_models.Article.objects.create(
        journal=journal,
        title='Test Article from Utils Testing Helpers',
        article_agreement='Test Article',
        section=create_section(journal),
    )

    if kwargs.pop('with_author', False):
        kwargs = {
            'salutation': 'Dr.',
            'name_suffix': 'Jr.',
            'orcid': '1234-5678-9012-345X',
            'email': '{}{}'.format(uuid4(), settings.DUMMY_EMAIL_DOMAIN)
        }
        author = create_author(journal, **kwargs)
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


def create_galley(article, file_obj=None):
    galley = core_models.Galley.objects.create(
        article_id=article.pk,
        file=file_obj,
    )
    return galley

def create_section(journal):

    section, created = sm_models.Section.objects.get_or_create(
        journal=journal,
        number_of_reviewers=2,
        name='Article',
        plural='Articles'
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


def create_review_form(journal):
    return review_models.ReviewForm.objects.create(
        name="A Form",
        slug="A Slug",
        intro="i",
        thanks="t",
        journal=journal
    )

def create_review_assignment(
        journal=None,
        article=None,
        reviewer=None,
        editor=None,
        due_date=None,
        review_form=None,
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

    return review_models.ReviewAssignment.objects.create(
        article=article,
        reviewer=reviewer,
        editor=editor,
        date_due=due_date,
        form=review_form
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
