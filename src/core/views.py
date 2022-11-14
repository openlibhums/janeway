__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from importlib import import_module
import json
import pytz
import time
import datetime

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.urls import NoReverseMatch, reverse
from django.shortcuts import render, get_object_or_404, redirect, Http404
from django.template.defaultfilters import linebreaksbr
from django.utils import timezone
from django.http import HttpResponse, QueryDict
from django.contrib.sessions.models import Session
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.conf import settings as django_settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils import translation
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views import generic

from core import models, forms, logic, workflow, models as core_models
from security.decorators import (
    editor_user_required, article_author_required, has_journal,
    any_editor_user_required,
)
from submission import models as submission_models
from review import models as review_models
from copyediting import models as copyedit_models
from production import models as production_models
from journal import models as journal_models
from proofing import logic as proofing_logic
from proofing import models as proofing_models
from utils import models as util_models, setting_handler, orcid
from utils.logger import get_logger
from utils.logic import get_janeway_version
from utils.decorators import GET_language_override
from utils.shared import language_override_redirect
from utils.logic import get_janeway_version
from repository import models as rm
from events import logic as events_logic


logger = get_logger(__name__)


def user_login(request):
    """
    Allows an unauthenticated user to login
    :param request: HttpRequest
    :return: HttpResponse
    """
    if request.user.is_authenticated():
        messages.info(request, 'You are already logged in.')
        if request.GET.get('next'):
            return redirect(request.GET.get('next'))
        else:
            return redirect(reverse('website_index'))
    else:
        bad_logins = logic.check_for_bad_login_attempts(request)

    if bad_logins >= 10:
        messages.info(
                request,
                'You have been banned from logging in due to failed attempts.'
        )
        logger.warning("[LOGIN_DENIED][FAILURES:%d]" % bad_logins)
        return redirect(reverse('website_index'))

    form = forms.LoginForm(bad_logins=bad_logins)

    if request.POST:
        form = forms.LoginForm(request.POST, bad_logins=bad_logins)

        if form.is_valid():
            user = request.POST.get('user_name').lower()
            pawd = request.POST.get('user_pass')

            user = authenticate(username=user, password=pawd)

            if user is not None:
                login(request, user)
                messages.info(request, 'Login successful.')
                logic.clear_bad_login_attempts(request)

                orcid_token = request.POST.get('orcid_token', None)
                if orcid_token:
                    try:
                        token_obj = models.OrcidToken.objects.get(token=orcid_token, expiry__gt=timezone.now())
                        user.orcid = token_obj.orcid
                        user.save()
                        token_obj.delete()
                    except models.OrcidToken.DoesNotExist:
                        pass

                if request.GET.get('next'):
                    return redirect(request.GET.get('next'))
                elif request.journal:
                    return redirect(reverse('core_dashboard'))
                else:
                    return redirect(reverse('website_index'))
            else:

                empty_password_check = logic.no_password_check(request.POST.get('user_name').lower())

                if empty_password_check:
                    messages.add_message(request, messages.INFO,
                                         'Password reset process has been initiated, please check your inbox for a'
                                         ' reset request link.')
                    logic.start_reset_process(request, empty_password_check)
                else:

                    messages.add_message(
                        request, messages.ERROR,
                        'Wrong email/password combination or your'
                        ' email addressed has not been confirmed yet.',
                    )
                    util_models.LogEntry.add_entry(types='Authentication',
                                                   description='Failed login attempt for user {0}'.format(
                                                       request.POST.get('user_name')),
                                                   level='Info', actor=None, request=request)
                    logic.add_failed_login_attempt(request)

    context = {
        'form': form,
    }
    template = 'core/login.html'

    return render(request, template, context)


def user_login_orcid(request):
    """
    Allows a user to login with ORCiD
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    orcid_code = request.GET.get('code', None)

    if orcid_code and django_settings.ENABLE_ORCID:
        orcid_id = orcid.retrieve_tokens(
            orcid_code,
            request.site_type,
        )

        if orcid_id:
            try:
                user = models.Account.objects.get(orcid=orcid_id)
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)

                if request.GET.get('next'):
                    return redirect(request.GET.get('next'))
                elif request.journal:
                    return redirect(reverse('core_dashboard'))
                else:
                    return redirect(reverse('website_index'))

            except models.Account.DoesNotExist:
                # Lookup ORCID email addresses
                orcid_details = orcid.get_orcid_record_details(orcid_id)
                for email in orcid_details.get("emails"):
                    candidates = models.Account.objects.filter(email=email)
                    if candidates.exists():
                        # Store ORCID for future authentication requests
                        candidates.update(orcid=orcid_id)
                        login(request, candidates.first())
                        if request.GET.get('next'):
                            return redirect(request.GET.get('next'))
                        elif request.journal:
                            return redirect(reverse('core_dashboard'))
                        else:
                            return redirect(reverse('website_index'))

                # Prepare ORCID Token for registration and redirect
                models.OrcidToken.objects.filter(orcid=orcid_id).delete()
                new_token = models.OrcidToken.objects.create(orcid=orcid_id)

                return redirect(reverse('core_orcid_registration', kwargs={'token': new_token.token}))
        else:
            messages.add_message(
                request,
                messages.WARNING,
                'Valid ORCiD not returned, please try again, or login with your username and password.'
            )
            return redirect(reverse('core_login'))
    else:
        messages.add_message(
            request,
            messages.WARNING,
            'No authorisation code provided, please try again or login with your username and password.')
        return redirect(reverse('core_login'))


@login_required
def user_logout(request):
    """
    Logs a user session out.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    messages.info(request, 'You have been logged out.')
    logout(request)
    return redirect(reverse('website_index'))


def get_reset_token(request):
    """
    Generates a password reset token and emails it to the user's email account
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    new_reset_token = None

    if request.POST:
        email_address = request.POST.get('email_address')
        messages.add_message(request, messages.INFO, 'If your account was found, an email has been sent to you.')
        try:
            account = models.Account.objects.get(email__iexact=email_address)
            logic.start_reset_process(request, account)
            return redirect(reverse('core_login'))
        except models.Account.DoesNotExist:
            return redirect(reverse('core_login'))

    template = 'core/accounts/get_reset_token.html'
    context = {
        'new_reset_token': new_reset_token,
    }

    return render(request, template, context)


def reset_password(request, token):
    """
    Takes a reset token and checks if it is valid then allows a user to reset their password, adter it expires the token
    :param request: HttpRequest
    :param token: string, PasswordResetToken.token
    :return: HttpResponse object
    """
    reset_token = get_object_or_404(models.PasswordResetToken, token=token, expired=False)
    form = forms.PasswordResetForm()

    if reset_token.has_expired():
        raise Http404

    if request.POST:
        form = forms.PasswordResetForm(request.POST)

        password_policy_check = logic.password_policy_check(request)

        if password_policy_check:
            for policy_fail in password_policy_check:
                form.add_error('password_1', policy_fail)

        if form.is_valid():
            password = form.cleaned_data['password_2']
            reset_token.account.set_password(password)
            reset_token.account.is_active = True
            logic.clear_bad_login_attempts(request)
            reset_token.account.save()
            reset_token.expired = True
            reset_token.save()
            messages.add_message(request, messages.SUCCESS, 'Your password has been reset.')
            return redirect(reverse('core_login'))

    template = 'core/accounts/reset_password.html'
    context = {
        'reset_token': reset_token,
        'form': form,
    }

    return render(request, template, context)


def register(request):
    """
    Displays a form for users to register with the journal. If the user is registering on a journal we give them
    the Author role.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    initial = {}
    token, token_obj = request.GET.get('token', None), None
    if token:
        token_obj = get_object_or_404(models.OrcidToken, token=token)
        orcid_details = orcid.get_orcid_record_details(token_obj.orcid)
        initial["first_name"] = orcid_details.get("first_name")
        initial["last_name"] = orcid_details.get("last_name")
        if orcid_details.get("emails"):
            initial["email"] = orcid_details["emails"][0]

    form = forms.RegistrationForm(
        journal=request.journal,
        initial=initial,
    )

    if request.POST:
        form = forms.RegistrationForm(
            request.POST,
            journal=request.journal,
        )

        password_policy_check = logic.password_policy_check(request)

        if password_policy_check:
            for policy_fail in password_policy_check:
                form.add_error('password_1', policy_fail)

        if form.is_valid():
            if token_obj:
                new_user = form.save(commit=False)
                new_user.orcid = token_obj.orcid
                new_user.save()
                token_obj.delete()
                # If the email matches the user email on ORCID, log them in
                if new_user.email == initial.get("email"):
                    new_user.is_active = True
                    new_user.save()
                    login(request, new_user)
                    if request.GET.get('next'):
                        return redirect(request.GET.get('next'))
                    elif request.journal:
                        return redirect(reverse('core_dashboard'))
                    else:
                        return redirect(reverse('website_index'))
            else:
                new_user = form.save()

            if request.journal:
                new_user.add_account_role('author', request.journal)
            logic.send_confirmation_link(request, new_user)

            messages.add_message(request, messages.SUCCESS, 'Your account has been created, please follow the'
                                                            'instructions in the email that has been sent to you.')
            return redirect(reverse('core_login'))

    template = 'core/accounts/register.html'
    context = {
        'form': form,
    }

    return render(request, template, context)


def orcid_registration(request, token):
    token = get_object_or_404(models.OrcidToken, token=token, expiry__gt=timezone.now())

    template = 'core/accounts/orcid_registration.html'
    context = {
        'token': token,
    }

    return render(request, template, context)


def activate_account(request, token):
    """
    Activates a user account if an Account object with the
    matching token is found and is not already active.
    :param request: HttpRequest object
    :param token: string, Account.confirmation_token
    :return: HttpResponse object
    """
    try:
        account = models.Account.objects.get(confirmation_code=token, is_active=False)
    except models.Account.DoesNotExist:
        account = None

    if account and request.POST:
        account.is_active = True
        account.confirmation_code = None
        account.save()

        messages.add_message(
            request,
            messages.SUCCESS,
            'Account activated',
        )

        return redirect(reverse('core_login'))

    template = 'core/accounts/activate_account.html'
    context = {
        'account': account,
    }

    return render(request, template, context)


@login_required
def edit_profile(request):
    """
    Allows a user to edit their own profile, reset their password or change their email address.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    user = request.user

    form = forms.EditAccountForm(instance=user)

    if request.POST:
        if 'email' in request.POST:
            email_address = request.POST.get('email_address')
            try:
                validate_email(email_address)
                try:
                    logic.handle_email_change(request, email_address)
                    return redirect(reverse('website_index'))
                except IntegrityError:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        'An account with that email address already exists.',
                    )
            except ValidationError:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'Email address is not valid.',
                )

        elif 'change_password' in request.POST:
            old_password = request.POST.get('current_password')
            new_pass_one = request.POST.get('new_password_one')
            new_pass_two = request.POST.get('new_password_two')

            if old_password and request.user.check_password(old_password):

                if new_pass_one == new_pass_two:
                    problems = request.user.password_policy_check(request, new_pass_one)
                    if not problems:
                        request.user.set_password(new_pass_one)
                        request.user.save()
                        messages.add_message(request, messages.SUCCESS, 'Password updated.')
                    else:
                        [messages.add_message(request, messages.INFO, problem) for problem in problems]
                else:
                    messages.add_message(request, messages.WARNING, 'Passwords do not match')

            else:
                messages.add_message(request, messages.WARNING, 'Old password is not correct.')

        elif 'subscribe' in request.POST and request.journal:
            request.user.add_account_role(
                'reader',
                request.journal,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                'Successfully subscribed to article notifications.',
            )

        elif 'unsubscribe' in request.POST and request.journal:
            request.user.remove_account_role(
                'reader',
                request.journal
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                'Successfully unsubscribed from article notifications.',
            )

        elif 'edit_profile' in request.POST:
            form = forms.EditAccountForm(request.POST, request.FILES, instance=user)

            if form.is_valid():
                form.save()
                messages.add_message(request, messages.SUCCESS, 'Profile updated.')
                return redirect(reverse('core_edit_profile'))

        elif 'export' in request.POST:
            return logic.export_gdpr_user_profile(user)

    template = 'core/accounts/edit_profile.html'
    context = {
        'form': form,
        'user_to_edit': user,
    }

    return render(request, template, context)


def public_profile(request, uuid):
    """
    A page that displays a user's public profile if they have enabled display
    :param request: django HTTPRequest object
    :param uuid: a uuid4 string
    :return: HTTPResponse
    """

    user = get_object_or_404(
        models.Account,
        uuid=uuid,
        is_active=True,
        enable_public_profile=True,
    )
    roles = models.AccountRole.objects.filter(
        user=user,
        journal=request.journal,
    )

    template = 'core/accounts/public_profile.html'
    context = {
        'user': user,
        'roles': roles,
    }

    return render(request, template, context)


@has_journal
@login_required
def dashboard(request):
    """
    Displays a dashboard for authenticated users.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    template = 'core/dashboard.html'
    new_proofing, active_proofing, completed_proofing = proofing_logic.get_tasks(request)
    new_proofing_typesetting, active_proofing_typesetting, completed_proofing_typesetting = proofing_logic.get_typesetting_tasks(request)
    section_editor_articles = review_models.EditorAssignment.objects.filter(editor=request.user,
                                                                            editor_type='section-editor',
                                                                            article__journal=request.journal)

    # TODO: Move most of this to model logic.
    context = {
        'new_proofing': new_proofing.count(),
        'active_proofing': active_proofing.count(),
        'completed_proofing': completed_proofing.count(),
        'new_proofing_typesetting': new_proofing_typesetting.count(),
        'completed_proofing_typesetting': completed_proofing_typesetting.count(),
        'active_proofing_typesetting': active_proofing_typesetting.count(),
        'unassigned_articles_count': submission_models.Article.objects.filter(
            stage=submission_models.STAGE_UNASSIGNED, journal=request.journal).count(),
        'assigned_articles_count': submission_models.Article.objects.filter(
            Q(stage=submission_models.STAGE_ASSIGNED) | Q(stage=submission_models.STAGE_UNDER_REVIEW) | Q(
                stage=submission_models.STAGE_UNDER_REVISION), journal=request.journal).count(),
        'editing_articles_count': submission_models.Article.objects.filter(
            Q(stage=submission_models.STAGE_EDITOR_COPYEDITING) | Q(
                stage=submission_models.STAGE_AUTHOR_COPYEDITING) | Q(
                stage=submission_models.STAGE_FINAL_COPYEDITING), journal=request.journal).count(),
        'production_articles_count': submission_models.Article.objects.filter(
            Q(stage=submission_models.STAGE_TYPESETTING), journal=request.journal).count(),
        'proofing_articles_count': submission_models.Article.objects.filter(
            Q(stage=submission_models.STAGE_PROOFING), journal=request.journal).count(),
        'prepub_articles_count': submission_models.Article.objects.filter(
            Q(stage=submission_models.STAGE_READY_FOR_PUBLICATION), journal=request.journal).count(),
        'is_editor': request.user.is_editor(request),
        'is_author': request.user.is_author(request),
        'is_reviewer': request.user.is_reviewer(request),
        'section_editor_articles': section_editor_articles,
        'active_submission_count': submission_models.Article.objects.filter(
            owner=request.user,
            journal=request.journal).exclude(
            stage=submission_models.STAGE_UNSUBMITTED).count(),
        'in_progress_submission_count': submission_models.Article.objects.filter(owner=request.user,
                                                                                 journal=request.journal,
                                                                                 stage=submission_models.
                                                                                 STAGE_UNSUBMITTED).count(),
        'assigned_articles_for_user_review_count': review_models.ReviewAssignment.objects.filter(
            Q(is_complete=False) &
            Q(reviewer=request.user) &
            Q(article__stage=submission_models.STAGE_UNDER_REVIEW) &
            Q(date_accepted__isnull=True), article__journal=request.journal).count(),
        'assigned_articles_for_user_review_accepted_count': review_models.ReviewAssignment.objects.filter(
            Q(is_complete=False) &
            Q(reviewer=request.user) &
            Q(article__stage=submission_models.STAGE_UNDER_REVIEW) &
            Q(date_accepted__isnull=False), article__journal=request.journal).count(),
        'assigned_articles_for_user_review_completed_count': review_models.ReviewAssignment.objects.filter(
            Q(is_complete=True) &
            Q(reviewer=request.user) &
            Q(date_declined__isnull=True), article__journal=request.journal).count(),

        'copyeditor_requests': copyedit_models.CopyeditAssignment.objects.filter(
            Q(copyeditor=request.user) &
            Q(decision__isnull=True) &
            Q(copyedit_reopened__isnull=True), article__journal=request.journal).count(),
        'copyeditor_accepted_requests': copyedit_models.CopyeditAssignment.objects.filter(
            Q(copyeditor=request.user, decision='accept', copyeditor_completed__isnull=True,
              article__journal=request.journal) |
            Q(copyeditor=request.user, decision='accept', copyeditor_completed__isnull=False,
              article__journal=request.journal, copyedit_reopened__isnull=False,
              copyedit_reopened_complete__isnull=True)
        ).count(),
        'copyeditor_completed_requests': copyedit_models.CopyeditAssignment.objects.filter(
            (Q(copyeditor=request.user) & Q(copyeditor_completed__isnull=False)) |
            (Q(copyeditor=request.user) & Q(copyeditor_completed__isnull=False) &
             Q(copyedit_reopened_complete__isnull=False)), article__journal=request.journal).count(),

        'typeset_tasks': production_models.TypesetTask.active_objects.filter(
            assignment__article__journal=request.journal,
            accepted__isnull=True,
            completed__isnull=True,
            typesetter=request.user).count(),
        'typeset_in_progress_tasks': production_models.TypesetTask.active_objects.filter(
            assignment__article__journal=request.journal,
            accepted__isnull=False,
            completed__isnull=True,
            typesetter=request.user).count(),
        'typeset_completed_tasks': production_models.TypesetTask.active_objects.filter(
            assignment__article__journal=request.journal,
            accepted__isnull=False,
            completed__isnull=False,
            typesetter=request.user).count(),
        'active_submissions': submission_models.Article.objects.filter(
            authors=request.user,
            journal=request.journal
        ).exclude(
            stage__in=[submission_models.STAGE_UNSUBMITTED, submission_models.STAGE_PUBLISHED],
        ).order_by('-date_submitted'),
        'published_submissions': submission_models.Article.objects.filter(
            authors=request.user,
            journal=request.journal,
            stage=submission_models.STAGE_PUBLISHED,
        ).order_by('-date_published'),
        'progress_submissions': submission_models.Article.objects.filter(
            journal=request.journal,
            owner=request.user,
            stage=submission_models.STAGE_UNSUBMITTED).order_by('-date_started'),
        'workflow_elements': workflow.element_names(request.journal.workflow().elements.all()),
        'workflow_element_url': request.GET.get('workflow_element_url', False)
    }

    return render(request, template, context)


@has_journal
@any_editor_user_required
def active_submissions(request):
    template = 'core/active_submissions.html'

    active_submissions = submission_models.Article.objects.exclude(
            stage=submission_models.STAGE_PUBLISHED).exclude(
            stage=submission_models.STAGE_REJECTED).exclude(
            stage=submission_models.STAGE_UNSUBMITTED).filter(
            journal=request.journal
        ).order_by('pk', 'title')

    if not request.user.is_editor(request) and request.user.is_section_editor(request):
        active_submissions = logic.filter_articles_to_editor_assigned(
            request,
            active_submissions
        )

    context = {
        'active_submissions': active_submissions,
        'sections': submission_models.Section.objects.filter(is_filterable=True,
                                                             journal=request.journal),
        'workflow_element_url': request.GET.get('workflow_element_url', False)
    }

    return render(request, template, context)


@has_journal
@any_editor_user_required
def active_submission_filter(request):
    articles = logic.build_submission_list(request)
    html = ''

    for article in articles:
        html = html + logic.create_html_snippet('article', article, 'elements/core/submission_list_element.html')

    if not articles:
        html = '<p>There are no articles to display</p>'

    return HttpResponse(json.dumps({'status': 200, 'html': html}))


@has_journal
@article_author_required
def dashboard_article(request, article_id):
    """
    Displays information about an article to its author only.
    :param request: HttpRequest object
    :param article_id: int, Article object primary key
    :return: HttpResponse object
    """
    article = get_object_or_404(submission_models.Article, pk=article_id)

    template = 'core/article.html'
    context = {
        'article': article,
    }

    return render(request, template, context)


@editor_user_required
def manager_index(request):
    """
    Displays the manager index if there is a journal, if not redirects the user to the press manager index.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    if not request.journal:
        from press import views as press_views
        return press_views.manager_index(request)

    template = 'core/manager/index.html'

    support_message = logic.render_nested_setting(
        'support_contact_message_for_staff',
        'general',
        request,
        nested_settings=[('support_email','general')],
    )

    context = {
        'published_articles': submission_models.Article.objects.filter(
            date_published__isnull=False,
            stage=submission_models.STAGE_PUBLISHED,
            journal=request.journal
        ).select_related('section')[:25],
        'support_message': support_message,
        'version': get_janeway_version(),
    }
    return render(request, template, context)


@staff_member_required
def flush_cache(request):
    """
    Flushes Django's cache
    :param request: HttpRequest object
    :return: HttpRedirect
    """
    cache.clear()
    messages.add_message(request, messages.SUCCESS, 'Cache has been flushed.')

    return redirect(reverse('core_manager_index'))


@editor_user_required
def settings_index(request):
    """
    Displays a list of all settings objects.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    template = 'core/manager/settings/index.html'
    context = {
        'settings': models.Setting.objects.order_by('name')
    }

    return render(request, template, context)


@staff_member_required
def default_settings_index(request):
    """ Proxy view for edit_setting allowing to edit defaults

    :param request: HttpRequest object
    :return: HttpResponse object
    """
    if request.journal:
        raise Http404()

    return settings_index(request)


@GET_language_override
@editor_user_required
def edit_setting(request, setting_group, setting_name):
    """
    Allows a user to edit a setting. Fields are auto generated based on the setting.kind field
    :param request: HttpRequest object
    :param setting_group: string, SettingGroup.name
    :param setting_name: string, Setting.name
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        setting = models.Setting.objects.get(
                name=setting_name, group__name=setting_group)
        setting_value = setting_handler.get_setting(
                setting_group,
                setting_name,
                request.journal,
                default=False
            )

        if setting_value and setting_value.setting.types == 'rich-text':
            setting_value.value = linebreaksbr(setting_value.value)

        edit_form = forms.EditKey(
                key_type=setting.types,
                value=setting_value.value if setting_value else None
        )

        if request.POST and 'delete' in request.POST and setting_value:
            setting_value.delete()

            return redirect(reverse('core_settings_index'))

        if request.POST:
            if 'delete' in request.POST and setting_value:
                setting_value.delete()
            else:
                value = request.POST.get('value')
                if request.FILES:
                    value = logic.handle_file(request, setting_value, request.FILES['value'])

                try:
                    setting_value = setting_handler.save_setting(
                        setting_group, setting_name, request.journal, value)
                except ValidationError as error:
                    messages.add_message( request, messages.ERROR, error)
                else:
                    cache.clear()

            return language_override_redirect(
                request,
                'core_edit_setting',
                {'setting_group': setting_group, 'setting_name': setting_name},
            )

        template = 'core/manager/settings/edit_setting.html'
        context = {
            'setting': setting,
            'setting_value': setting_value,
            'group': setting.group,
            'edit_form': edit_form,
            'value': setting_value.value if setting_value else None
        }
        return render(request, template, context)


@staff_member_required
def edit_default_setting(request, setting_group, setting_name):
    """ Proxy view for edit_setting allowing editing the default value

    :param request: HttpRequest object
    :param setting_group: string, SettingGroup.name
    :param setting_name: string, Setting.name
    :return: HttpResponse object
    """
    return edit_setting(request, setting_group, setting_name)


@GET_language_override
@editor_user_required
def edit_settings_group(request, display_group):
    """
    Displays a group of settings on a page for editing. If there is no request.journal we are editing from the press
    and must set a temp request.journal and then unset it.
    :param request: HttpRequest object
    :param display_group: string, name of a group of settings
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        settings, setting_group = logic.get_settings_to_edit(display_group, request.journal)
        edit_form = forms.GeneratedSettingForm(settings=settings)
        attr_form_object, attr_form, display_tabs, fire_redirect = None, None, True, True

        if display_group == 'journal':
            attr_form_object = forms.JournalAttributeForm
        elif display_group == 'images':
            attr_form_object = forms.JournalImageForm
            display_tabs = False
        elif display_group == 'article':
            attr_form_object = forms.JournalArticleForm
            display_tabs = False
        elif display_group == 'styling':
            attr_form_object = forms.JournalStylingForm
            display_tabs = False
        elif display_group == 'submission':
            attr_form_object = forms.JournalSubmissionForm

        if attr_form_object:
            attr_form = attr_form_object(instance=request.journal)

        if not settings and not attr_form_object:
            raise Http404

        if request.POST:
            edit_form = forms.GeneratedSettingForm(
                request.POST,
                settings=settings,
            )

            if edit_form.is_valid():
                edit_form.save(
                    group=setting_group,
                    journal=request.journal,
                )
            else:
                fire_redirect = False

            if attr_form_object:
                attr_form = attr_form_object(
                    request.POST,
                    request.FILES,
                    instance=request.journal,
                )
                if attr_form.is_valid():
                    attr_form.save()

                    if display_group == 'images':
                        logic.handle_default_thumbnail(request, request.journal, attr_form)
                else:
                    fire_redirect = False

            cache.clear()

            if fire_redirect:
                return language_override_redirect(
                    request,
                    'core_edit_settings_group',
                    {'display_group': display_group},
                )

        template = 'admin/core/manager/settings/group.html'
        context = {
            'group': display_group,
            'settings_list': settings,
            'edit_form': edit_form,
            'attr_form': attr_form,
            'display_tabs': display_tabs,
        }

        return render(request, template, context)


@editor_user_required
def edit_plugin_settings_groups(request, plugin, setting_group_name, journal=None, title=None):
    """
    Allows for editing a group of plugin settings
    :param request: HttpRequest object
    :param plugin: string, short name of a plugin
    :param setting_group_name: string, name of a group of settings
    :param journal: an optional argument, Journal object
    :param title: an optional argument, page title, string
    :return: HttpResponse object
    """
    if journal != '0':
        journal = journal_models.Journal.objects.get(fk=int(journal))
    else:
        journal = None

    from utils import models as utils_models
    plugin = utils_models.Plugin.objects.get(name=plugin)

    module_name = "{0}.{1}.plugin_settings".format("plugins", plugin.name)
    plugin_settings = import_module(module_name)
    manager_url = getattr(plugin_settings, 'MANAGER_URL', '')
    settings = getattr(plugin_settings, setting_group_name, '')()

    if not settings:
        raise Http404

    edit_form = forms.GeneratedPluginSettingForm(settings=settings)

    if request.POST:
        edit_form = forms.GeneratedPluginSettingForm(request.POST, settings=settings)

        if edit_form.is_valid():
            edit_form.save(plugin=plugin, journal=journal)
            cache.clear()

            return redirect(reverse(request.GET['return']))

    if not title:
        title = plugin.best_name()

    template = 'core/manager/settings/plugin.html'
    context = {
        'plugin': plugin,
        'settings': settings,
        'edit_form': edit_form,
        'title': title,
        'manager_url': manager_url,
    }

    return render(request, template, context)


@editor_user_required
def roles(request):
    """
    Displays a list of the journal roles
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    template = 'core/manager/roles/roles.html'

    roles = models.Role.objects.all().exclude(slug='reader')
    for role in roles:
        role.user_count = request.journal.users_with_role_count(role.slug)

    context = {
        'roles': roles,
    }

    return render(request, template, context)


@editor_user_required
def role(request, slug):
    """
    Displays details of a single role.
    :param request: HttpRequest object
    :param slug: string, matches Role.slug
    :return: HttpResponse object
    """
    role_obj = get_object_or_404(models.Role, slug=slug)

    account_roles = models.AccountRole.objects.filter(journal=request.journal, role=role_obj)

    template = 'core/manager/roles/role.html'
    context = {
        'role': role_obj,
        'account_roles': account_roles
    }

    return render(request, template, context)


@editor_user_required
def role_action(request, slug, user_id, action):
    """
    Either adds or removes a user from a role depending on the action supplied.
    :param request: HttpRequest object
    :param slug: string, matches Roles.slug
    :param user_id: Account object PK
    :param action: string, either 'add' or 'remove'
    :return: HttpResponse object
    """
    user = get_object_or_404(models.Account, pk=user_id)
    role_obj = get_object_or_404(models.Role, slug=slug)

    if action == 'add':
        user.add_account_role(role_slug=slug, journal=request.journal)
    elif action == 'remove':
        user.remove_account_role(role_slug=slug, journal=request.journal)

    user.save()

    return redirect(reverse('core_manager_role', kwargs={'slug': role_obj.slug}))


@editor_user_required
def users(request):
    """
    Displays a list of users, allows multiple users to be added to a role.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    if request.POST:
        users = request.POST.getlist('users')
        role = request.POST.get('role')
        logic.handle_add_users_to_role(users, role, request)
        return redirect(reverse('core_manager_users'))

    template = 'core/manager/users/index.html'
    context = {
        'users': request.journal.journal_users(objects=True),
        'roles': models.Role.objects.all().order_by(('name')),
    }
    return render(request, template, context)


@editor_user_required
def add_user(request):
    """
    Displays a form for adding users to JW,
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    form = forms.EditAccountForm()
    registration_form = forms.AdminUserForm(active='add', request=request)
    return_url = request.GET.get('return', None)
    role = request.GET.get('role', None)

    if request.POST:
        registration_form = forms.AdminUserForm(
            request.POST,
            active='add',
            request=request
        )

        if registration_form.is_valid():
            new_user = registration_form.save()
            # Every new user is given the author role
            new_user.add_account_role('author', request.journal)

            if role:
                new_user.add_account_role(role, request.journal)

            form = forms.EditAccountForm(
                request.POST,
                request.FILES,
                instance=new_user
            )

            if form.is_valid():
                form.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'User created.'
                )

                if return_url:
                    return redirect(return_url)

                return redirect(reverse('core_manager_users'))

        else:
            # If the registration form is not valid,
            # we need to add post data to the Edit form for display.
            form = forms.EditAccountForm(request.POST)

    template = 'core/manager/users/edit.html'
    context = {
        'form': form,
        'registration_form': registration_form,
        'active': 'add',
    }
    return render(request, template, context)


@editor_user_required
def user_edit(request, user_id):
    """
    Allows an editor to edit an existing user account.
    :param request: HttpRequest object
    :param user_id: Account object PK
    :return: HttpResponse object
    """
    user = models.Account.objects.get(pk=user_id)
    form = forms.EditAccountForm(instance=user)
    registration_form = forms.AdminUserForm(instance=user, request=request)

    if request.POST:
        form = forms.EditAccountForm(request.POST, request.FILES, instance=user)
        registration_form = forms.AdminUserForm(request.POST, instance=user, request=request)

        if form.is_valid() and registration_form.is_valid():
            registration_form.save()
            form.save()
            messages.add_message(request, messages.SUCCESS, 'Profile updated.')

            return redirect(reverse('core_manager_users'))

    template = 'core/manager/users/edit.html'
    context = {
        'user_to_edit': user,
        'form': form,
        'registration_form': registration_form,
        'active': 'update',
    }
    return render(request, template, context)


@staff_member_required
def inactive_users(request):
    """
    Displays a list of inactive user accounts.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    user_list = models.Account.objects.filter(is_active=False)

    template = 'core/manager/users/inactive.html'
    context = {
        'users': user_list,
    }

    return render(request, template, context)


@staff_member_required
def logged_in_users(request):
    """
    Gets a list of authenticated users whose sessions have not expired yet.
    :param request: django request object
    :return: contextualised django template
    """
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_id_list = list()

    for session in sessions:
        data = session.get_decoded()
        user_id_list.append(data.get('_auth_user_id', None))

    users = models.Account.objects.filter(id__in=user_id_list)

    template = 'core/manager/users/logged_in_users.html'
    context = {
        'users': users,
    }

    return render(request, template, context)


@editor_user_required
def user_history(request, user_id):
    """
    Displays a user's editorial history.
    :param request: django HTTPRequest object
    :param user_id: core.User primary key
    :return: a rendered template
    """

    user = get_object_or_404(models.Account, pk=user_id)
    content_type = ContentType.objects.get_for_model(user)
    log_entries = util_models.LogEntry.objects.filter(
        content_type=content_type,
        object_id=user.pk,
        is_email=True,
    )

    template = 'core/manager/users/history.html'
    context = {
        'user': user,
        'review_assignments': review_models.ReviewAssignment.objects.filter(
            reviewer=user,
            article__journal=request.journal,
        ),
        'copyedit_assignments':
            copyedit_models.CopyeditAssignment.objects.filter(
                copyeditor=user,
                article__journal=request.journal,
            ),
        'log_entries': log_entries,
    }

    return render(request, template, context)


@editor_user_required
def enrol_users(request):
    user_search = []
    first_name = request.GET.get('first_name', '')
    last_name = request.GET.get('last_name', '')
    email = request.GET.get('email', '')

    if first_name or last_name or email:
        filters = {}
        if first_name and len(first_name) >= 2:
            filters['first_name__icontains'] = first_name
        if last_name and len(last_name) >= 2:
            filters['last_name__icontains'] = last_name
        if email and len(email) >= 2:
            filters['email__icontains'] = email

        user_search = core_models.Account.objects.filter(**filters)

    template = 'core/manager/users/enrol_users.html'
    context = {
        'user_search': user_search,
        'roles': models.Role.objects.order_by(('name')),
        'first_name': first_name,
        'last_name': last_name,
        'email': email,
        'return': request.GET.get('return'),
        'reader': models.Role.objects.get(slug='reader'),
    }
    return render(request, template, context)


@editor_user_required
def settings_home(request):
    # this should return a context containing:
    # 1. An excluded list of homepage items
    # 2. A list of active homepage items

    active_elements = models.HomepageElement.objects.filter(content_type=request.model_content_type,
                                                            object_id=request.site_type.pk, active=True)
    active_pks = [f.pk for f in active_elements.all()]

    if request.press and not request.journal:
        elements = models.HomepageElement.objects.filter(content_type=request.model_content_type,
                                                         object_id=request.site_type.pk,
                                                         available_to_press=True).exclude(pk__in=active_pks)
    else:
        elements = models.HomepageElement.objects.filter(content_type=request.model_content_type,
                                                         object_id=request.site_type.pk).exclude(pk__in=active_pks)

    if 'add' in request.POST:
        element_id = request.POST.get('add')
        homepage_element = get_object_or_404(models.HomepageElement, pk=element_id,
                                             content_type=request.model_content_type, object_id=request.site_type.pk)
        if homepage_element.name == 'Carousel' and request.journal and not request.journal.default_large_image:
            messages.add_message(request, messages.WARNING, 'You cannot enable the carousel until you add a default'
                                                            'large image file.')
        else:
            homepage_element.active = True
            homepage_element.save()

        return redirect(reverse('home_settings_index'))

    if 'delete' in request.POST:
        element_id = request.POST.get('delete')
        homepage_element = get_object_or_404(models.HomepageElement, pk=element_id,
                                             content_type=request.model_content_type, object_id=request.site_type.pk)

        homepage_element.active = False
        homepage_element.save()

        return redirect(reverse('home_settings_index'))

    template = 'core/manager/settings/index_home.html'
    context = {
        'active_elements': active_elements,
        'elements': elements,
    }

    return render(request, template, context)


@editor_user_required
def journal_home_order(request):
    """
    Allows the re-ordering of homepage elements
    :param request: HttpRequest object
    :return: HttpResponse
    """
    if request.POST:
        ids = request.POST.getlist('element[]')
        ids = [int(_id) for _id in ids]

        for he in models.HomepageElement.objects.filter(content_type=request.model_content_type,
                                                        object_id=request.site_type.pk, active=True):
            he.sequence = ids.index(he.pk)
            he.save()

    return HttpResponse('Thanks')


@editor_user_required
def article_images(request):
    """
    Displays a list of articles for editing their images.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    articles = submission_models.Article.objects.filter(journal=request.journal)

    template = 'core/manager/images/articles.html'
    context = {
        'articles': articles,
    }

    return render(request, template, context)


@editor_user_required
def article_image_edit(request, article_pk):
    """
    Displays the images an article has and allows a user to upload new images for display. Resizes these images for
    best fit.
    :param request: HttpRequest object
    :param article_pk: Article object PK
    :return: HttpResponse object
    """
    article = get_object_or_404(submission_models.Article, pk=article_pk, journal=request.journal)
    article_meta_image_form = forms.ArticleMetaImageForm(instance=article)

    if 'delete' in request.POST:
        delete_id = request.POST.get('delete')
        file_to_delete = get_object_or_404(models.File, pk=delete_id, article_id=article_pk)
        article_files = [article.thumbnail_image_file, article.large_image_file]

        if file_to_delete in article_files and request.user.is_staff or request.user == file_to_delete.owner:
            file_to_delete.delete()

        return redirect(reverse('core_article_image_edit', kwargs={'article_pk': article.pk}))

    if request.POST and request.FILES and 'large' in request.POST:
        uploaded_file = request.FILES.get('image_file')
        logic.handle_article_large_image_file(uploaded_file, article, request)

    elif request.POST and request.FILES and 'thumb' in request.POST:
        uploaded_file = request.FILES.get('image_file')
        logic.handle_article_thumb_image_file(uploaded_file, article, request)

    elif request.POST and request.FILES and 'meta' in request.POST:
        article.unlink_meta_file()
        article_meta_image_form = forms.ArticleMetaImageForm(request.POST, request.FILES, instance=article)
        if article_meta_image_form.is_valid():
            article_meta_image_form.save()

    if request.POST:
        flush_cache(request)
        return redirect(reverse('core_article_image_edit', kwargs={'article_pk': article.pk}))

    template = 'core/manager/images/article_image.html'
    context = {
        'article': article,
        'article_meta_image_form': article_meta_image_form,
    }

    return render(request, template, context)


@editor_user_required
def contacts(request):
    """
    Allows for adding and deleting of JournalContact objects.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    form = forms.JournalContactForm()
    contacts = models.Contacts.objects.filter(
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
    )

    if 'delete' in request.POST:
        contact_id = request.POST.get('delete')
        contact = get_object_or_404(
            models.Contacts,
            pk=contact_id,
            content_type=request.model_content_type,
            object_id=request.site_type.pk,
        )
        contact.delete()
        return redirect(reverse('core_journal_contacts'))

    if request.POST:
        form = forms.JournalContactForm(request.POST)

        if form.is_valid():
            contact = form.save(commit=False)
            contact.content_type = request.model_content_type
            contact.object_id = request.site_type.pk
            contact.sequence = request.site_type.next_contact_order()
            contact.save()
            return redirect(reverse('core_journal_contacts'))

    template = 'core/manager/contacts/index.html'
    context = {
        'form': form,
        'contacts': contacts,
        'action': 'new',
    }

    return render(request, template, context)


@editor_user_required
@GET_language_override
def edit_contacts(request, contact_id=None):
    """
    Allows for editing of existing Contact objects
    :param request: HttpRequest object
    :param contact_id: Contact object PK
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        if contact_id:
            contact = get_object_or_404(
                models.Contacts,
                pk=contact_id,
                content_type=request.model_content_type,
                object_id=request.site_type.pk,
            )
            form = forms.JournalContactForm(instance=contact)
        else:
            contact = None
            form = forms.JournalContactForm(
                next_sequence=request.site_type.next_contact_order(),
            )

        if request.POST:
            form = forms.JournalContactForm(request.POST, instance=contact)

            if form.is_valid():
                if contact:
                    contact = form.save()
                else:
                    contact = form.save(commit=False)
                    contact.content_type = request.model_content_type
                    contact.object_id = request.site_type.pk
                    contact.save()

                return language_override_redirect(
                    request,
                    'core_journal_contact',
                    {'contact_id': contact.pk},
                )

    template = 'core/manager/contacts/manage.html'
    context = {
        'form': form,
        'contact': contact,
    }

    return render(request, template, context)


@editor_user_required
def contacts_order(request):
    """
    Reorders the Contact list, posted via AJAX.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    if request.POST:
        ids = request.POST.getlist('contact[]')
        ids = [int(_id) for _id in ids]

        for jc in models.Contacts.objects.filter(content_type=request.model_content_type, object_id=request.site_type.pk):
            jc.sequence = ids.index(jc.pk)
            jc.save()

    return HttpResponse('Thanks')


@editor_user_required
def editorial_team(request):
    """
    Displays a list of EditorialGroup objects, allows them to be deleted and created,
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    editorial_groups = models.EditorialGroup.objects.filter(journal=request.journal)

    if 'delete' in request.POST:
        delete_id = request.POST.get('delete')
        group = get_object_or_404(models.EditorialGroup, pk=delete_id, journal=request.journal)
        group.delete()
        return redirect(reverse('core_editorial_team'))

    template = 'core/manager/editorial/index.html'
    context = {
        'editorial_groups': editorial_groups,
    }

    return render(request, template, context)


@editor_user_required
@GET_language_override
def edit_editorial_group(request, group_id=None):
    """
    Allows editors to edit existing EditorialGroup objects
    :param request: HttpRequest object
    :param group_id: EditorialGroup object PK
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        if group_id:
            group = get_object_or_404(models.EditorialGroup, pk=group_id, journal=request.journal)
            form = forms.EditorialGroupForm(
                instance=group,
            )
        else:
            group = None
            form = forms.EditorialGroupForm(
                next_sequence=request.journal.next_group_order(),
            )

        if request.POST:
            form = forms.EditorialGroupForm(request.POST, instance=group)
            if form.is_valid():
                if group:
                    group = form.save()
                else:
                    group = form.save(commit=False)
                    group.journal = request.journal
                    group.save()

                return language_override_redirect(
                    request,
                    'core_edit_editorial_team',
                    {'group_id': group.pk},
                )

    template = 'core/manager/editorial/manage_group.html'
    context = {
        'group': group,
        'form': form,
    }

    return render(request, template, context)


@editor_user_required
def add_member_to_group(request, group_id, user_id=None):
    """
    Displays a list of users that are eligible to be added to an Editorial Group and displays those already in said
    group. Members can also be removed from Groups.
    :param request: HttpRequest object
    :param group_id: EditorialGroup object PK
    :param user_id: Account object PK, optional
    :return:
    """
    group = get_object_or_404(
        models.EditorialGroup,
        pk=group_id,
        journal=request.journal
    )
    journal_users = request.journal.journal_users(objects=True)
    members = [member.user for member in group.editorialgroupmember_set.all()]

    # Drop users thagit t are in both lists.
    user_list = list(set(journal_users) ^ set(members))

    if 'delete' in request.POST:
        delete_id = request.POST.get('delete')
        membership = get_object_or_404(
            models.EditorialGroupMember,
            pk=delete_id
        )
        membership.delete()
        return redirect(
            reverse(
                'core_editorial_member_to_group',
                kwargs={'group_id': group.pk}
            )
        )

    if user_id:
        user_to_add = get_object_or_404(models.Account, pk=user_id)
        if user_to_add not in members:
            models.EditorialGroupMember.objects.create(
                group=group,
                user=user_to_add,
                sequence=group.next_member_sequence()
            )
        return redirect(
            reverse(
                'core_editorial_member_to_group',
                kwargs={'group_id': group.pk}
            )
        )

    template = 'core/manager/editorial/add_member.html'
    context = {
        'group': group,
        'users': user_list,
    }

    return render(request, template, context)


@editor_user_required
def plugin_list(request):
    """
    Fetches a list of plugins and fetching their manager urls.
    :param request: HttpRequest object
    :return: HttpResponse object
    """

    plugin_list = list()
    failed_to_load = []

    if request.journal:
        plugins = util_models.Plugin.objects.filter(
            enabled=True,
            homepage_element=False,
        )
    else:
        plugins = util_models.Plugin.objects.filter(
            enabled=True,
            press_wide=True,
            homepage_element=False,
        )

    for plugin in plugins:
        try:
            module_name = "{0}.{1}.plugin_settings".format("plugins", plugin.name)
            plugin_settings = import_module(module_name)
            manager_url = getattr(plugin_settings, 'MANAGER_URL', '')
            if manager_url:
                reverse(manager_url)
            plugin_list.append(
                {'model': plugin,
                 'manager_url': manager_url,
                 'name': getattr(plugin_settings, 'PLUGIN_NAME')
                 },
            )
        except (ImportError, NoReverseMatch) as e:
            failed_to_load.append(plugin)
            logger.error("Importing plugin %s failed: %s" % (plugin, e))
            logger.exception(e)


    template = 'core/manager/plugins.html'
    context = {
        'plugins': plugin_list,
        'failed_to_load': failed_to_load,
    }

    return render(request, template, context)


@editor_user_required
def editorial_ordering(request, type_to_order, group_id=None):
    """
    Allows for drag and drop reordering of an editorialgroup
    :param request: HttpRequest object
    :param type_to_order: string, either 'group', 'sections', or 'member'
    :param group_id: EditorialGroup PK, optional
    :return: HttpRespons eobject
    """
    if type_to_order == 'group':
        ids = request.POST.getlist('group[]')
        objects = models.EditorialGroup.objects.filter(journal=request.journal)
    elif type_to_order == 'sections':
        ids = request.POST.getlist('section[]')
        objects = submission_models.Section.objects.filter(journal=request.journal)
    else:
        group = get_object_or_404(models.EditorialGroup, pk=group_id, journal=request.journal)
        ids = request.POST.getlist('member[]')
        objects = models.EditorialGroupMember.objects.filter(group=group)

    ids = [int(_id) for _id in ids]

    for _object in objects:
        _object.sequence = ids.index(_object.pk)
        _object.save()

    return HttpResponse('Thanks')


@has_journal
@editor_user_required
def kanban(request):
    """
    Displays lists of articles grouped by stage.
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    unassigned_articles = submission_models.Article.objects.filter(Q(stage=submission_models.STAGE_UNASSIGNED),
                                                                   journal=request.journal) \
        .order_by('-date_submitted')

    in_review = submission_models.Article.objects.filter(Q(stage=submission_models.STAGE_ASSIGNED) |
                                                         Q(stage=submission_models.STAGE_UNDER_REVIEW) |
                                                         Q(stage=submission_models.STAGE_UNDER_REVISION),
                                                         journal=request.journal) \
        .order_by('-date_submitted')

    copyediting = submission_models.Article.objects.filter(Q(stage=submission_models.STAGE_ACCEPTED) |
                                                           Q(stage__in=submission_models.COPYEDITING_STAGES),
                                                           journal=request.journal) \
        .order_by('-date_submitted')

    assigned_table = production_models.ProductionAssignment.objects.filter(article__journal=request.journal)
    assigned = [assignment.article.pk for assignment in assigned_table]

    prod_articles = submission_models.Article.objects.filter(
        stage=submission_models.STAGE_TYPESETTING, journal=request.journal)
    assigned_articles = submission_models.Article.objects.filter(pk__in=assigned)

    proofing_assigned_table = proofing_models.ProofingAssignment.objects.filter(
        article__journal=request.journal,
    )
    proofing_assigned = [assignment.article.pk for assignment in proofing_assigned_table]

    proof_articles = submission_models.Article.objects.filter(
        stage=submission_models.STAGE_PROOFING, journal=request.journal)
    proof_assigned_articles = submission_models.Article.objects.filter(
        pk__in=proofing_assigned,
    )

    prepub = submission_models.Article.objects.filter(
        Q(stage=submission_models.STAGE_READY_FOR_PUBLICATION),
        journal=request.journal,
    ).order_by('-date_submitted')

    articles_in_workflow_plugins = workflow.articles_in_workflow_plugins(request)

    context = {
        'unassigned_articles': unassigned_articles,
        'in_review': in_review,
        'copyediting': copyediting,
        'production': prod_articles,
        'production_assigned': assigned_articles,
        'proofing': proof_articles,
        'proofing_assigned': proof_assigned_articles,
        'prepubs': prepub,
        'articles_in_workflow_plugins': articles_in_workflow_plugins,
        'workflow': request.journal.workflow()
    }

    template = 'core/kanban.html'

    return render(request, template, context)


@editor_user_required
def delete_note(request, article_id, note_id):
    """
    Deletes Note objects
    :param request: HttpRequest object
    :param article_id: Article object PK
    :param note_id: Note object PK
    :return:
    """
    note = get_object_or_404(submission_models.Note, pk=note_id)
    note.delete()

    url = reverse('kanban_home')

    return redirect("{0}?article_id={1}".format(url, article_id))


@staff_member_required
def manage_notifications(request, notification_id=None):
    notifications = journal_models.Notifications.objects.filter(journal=request.journal)
    notification = None
    form = forms.NotificationForm()

    if notification_id:
        notification = get_object_or_404(journal_models.Notifications, pk=notification_id)
        form = forms.NotificationForm(instance=notification)

    if request.POST:
        if 'delete' in request.POST:
            delete_id = request.POST.get('delete')
            notification_to_delete = get_object_or_404(journal_models.Notifications, pk=delete_id)
            notification_to_delete.delete()
            return redirect(reverse('core_manager_notifications'))

        if notification:
            form = forms.NotificationForm(request.POST, instance=notification)
        else:
            form = forms.NotificationForm(request.POST)

        if form.is_valid():
            save_notification = form.save(commit=False)
            save_notification.journal = request.journal
            save_notification.save()

            return redirect(reverse('core_manager_notifications'))

    template = 'core/manager/notifications/manage_notifications.html'
    context = {
        'notifications': notifications,
        'notification': notification,
        'form': form,
    }

    return render(request, template, context)


@editor_user_required
def email_templates(request):
    """
    Displays a list of email templates
    :param request: HttpRequest object
    :return: HttpResponse object
    """
    template_list = (
        (setting, 'subject_%s' % setting.name)
        for setting in models.Setting.objects.filter(group__name='email')
    )

    template = 'core/manager/email/email_templates.html'
    context = {
        'template_list': template_list,
    }

    return render(request, template, context)


@editor_user_required
def section_list(request):
    """
    Displays a list of the journals sections.
    :praram request: HttpRequest object
    :return: HttpResponse
    """
    section_objects = submission_models.Section.objects.filter(
        journal=request.journal,
    )

    if request.POST and 'delete' in request.POST:
        section_id = request.POST.get('delete')
        section_to_delete = get_object_or_404(submission_models.Section, pk=section_id)

        if section_to_delete.article_count():
            messages.add_message(
                request,
                messages.WARNING,
                _(
                    'You cannot remove a section that contains articles. Remove articles'
                    ' from the section if you want to delete it.'
                ),
            )
        else:
            section_to_delete.delete()
        return redirect(reverse('core_manager_sections'))

    template = 'core/manager/sections/section_list.html'
    context = {
        'section_objects': section_objects,
    }
    return render(request, template, context)


@editor_user_required
@GET_language_override
def manage_section(request, section_id=None):
    """
    Displays a list of sections, allows them to be added, edited and deleted.
    :param request: HttpRequest object
    :param section_id: Section object PK, optional
    :return: HttpResponse object
    """
    with translation.override(request.override_language):
        section = get_object_or_404(submission_models.Section, pk=section_id,
                                    journal=request.journal) if section_id else None
        sections = submission_models.Section.objects.filter(journal=request.journal)

        if section:
            form = forms.SectionForm(instance=section, request=request)
        else:
            form = forms.SectionForm(request=request)

        if request.POST:

            if section:
                form = forms.SectionForm(request.POST, instance=section, request=request)
            else:
                form = forms.SectionForm(request.POST, request=request)

            if form.is_valid():
                form_section = form.save(commit=False)
                form_section.journal = request.journal
                form_section.save()
                form.save_m2m()

            return language_override_redirect(
                request,
                'core_manager_section',
                {'section_id': section.pk if section else form_section.pk},
            )

        template = 'core/manager/sections/manage_section.html'
        context = {
            'sections': sections,
            'section': section,
            'form': form,
        }
    return render(request, template, context)


@editor_user_required
def section_articles(request, section_id):
    """
    Displays a list of articles in a given section.
    """
    section = get_object_or_404(
        submission_models.Section,
        pk=section_id,
        journal=request.journal,
    )
    template = 'core/manager/sections/section_articles.html'
    context = {
        'section': section,
    }
    return render(request, template, context)


@editor_user_required
def pinned_articles(request):
    """
    Allows an Editor to pin articles to the top of the article page.
    :param request: HttpRequest object
    """
    pinned_articles = journal_models.PinnedArticle.objects.filter(journal=request.journal)
    published_articles = logic.get_unpinned_articles(request, pinned_articles)

    if request.POST:
        if 'pin' in request.POST:
            article_id = request.POST.get('pin')
            article = get_object_or_404(submission_models.Article, pk=article_id, journal=request.journal)
            journal_models.PinnedArticle.objects.create(
                article=article,
                journal=request.journal,
                sequence=request.journal.next_pa_seq())
            messages.add_message(request, messages.INFO, 'Article pinned.')

        if 'unpin' in request.POST:
            article_id = request.POST.get('unpin')
            pinned_article = get_object_or_404(journal_models.PinnedArticle, journal=request.journal, pk=article_id)
            pinned_article.delete()
            messages.add_message(request, messages.INFO, 'Article unpinned.')

        if 'orders[]' in request.POST:
            logic.order_pinned_articles(request, pinned_articles)

        return redirect(reverse('core_pinned_articles'))

    template = 'core/manager/pinned_articles.html'
    context = {
        'pinned_articles': pinned_articles,
        'published_articles': published_articles,
    }

    return render(request, template, context)


@has_journal
@staff_member_required
def journal_workflow(request):
    """
    Allows a staff member to setup workflows.
    :param request: django request object
    :return: template contextualised
    """
    journal_workflow, created = models.Workflow.objects.get_or_create(
        journal=request.journal
    )

    if created:
        workflow.create_default_workflow(request.journal)

    available_elements = logic.get_available_elements(journal_workflow)

    if request.POST:
        if 'element_name' in request.POST:
            element_name = request.POST.get('element_name')
            element = logic.handle_element_post(journal_workflow, element_name, request)
            if element:
                journal_workflow.elements.add(element)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    'Element added.'
                )
            else:
                messages.add_message(
                    request,
                    messages.WARNING,
                    'Element not found.'
                )

        if 'delete' in request.POST:
            delete_id = request.POST.get('delete')
            delete_element = get_object_or_404(
                models.WorkflowElement,
                journal=request.journal,
                pk=delete_id
            )
            workflow.remove_element(
                request,
                journal_workflow,
                delete_element
            )

        return redirect(reverse('core_journal_workflow'))

    template = 'core/workflow.html'
    context = {
        'workflow': journal_workflow,
        'available_elements': available_elements,
    }

    return render(request, template, context)


@staff_member_required
def order_workflow_elements(request):
    """
    Orders workflow elements based on their position in a list group.
    :param request: django request object
    :return: an http reponse
    """
    workflow = models.Workflow.objects.get(journal=request.journal)

    if request.POST:
        ids = [int(_id) for _id in request.POST.getlist('element[]')]

        for element in workflow.elements.all():
            order = ids.index(element.pk)
            element.order = order
            element.save()

    return HttpResponse('Thanks')


@ensure_csrf_cookie
@require_POST
def set_session_timezone(request):
    chosen_timezone = request.POST.get("chosen_timezone")
    response_data = {}
    if chosen_timezone in pytz.all_timezones_set:
        request.session["janeway_timezone"] = chosen_timezone
        status = 200
        response_data['message'] = 'OK'
        logger.debug("Timezone set to %s for this session" % chosen_timezone)
    else:
        status = 404
        response_data['message'] = 'Timezone not found: %s' % chosen_timezone
    response_data = {}

    return HttpResponse(
            content=json.dumps(response_data),
            content_type='application/json',
            status=200,
    )


@login_required
def request_submission_access(request):
    if request.repository:
        check = rm.RepositoryRole.objects.filter(
            repository=request.repository,
            user=request.user,
            role__slug='author',
        ).exists()
    elif request.journal:
        check = request.user.is_author(request)
    else:
        raise Http404('The Submission Access page is only accessible on Repository and Journal sites.')

    active_request = models.AccessRequest.objects.filter(
        user=request.user,
        journal=request.journal,
        repository=request.repository,
        processed=False,
    ).first()
    role = models.Role.objects.get(slug='author')
    form = forms.AccessRequestForm(
        journal=request.journal,
        repository=request.repository,
        user=request.user,
        role=role,
    )

    if request.POST and not active_request:
        form = forms.AccessRequestForm(
            request.POST,
            journal=request.journal,
            repository=request.repository,
            user=request.user,
            role=role,
        )
        if form.is_valid():
            access_request = form.save()
            event_kwargs = {
                'request': request,
                'access_request': access_request,
            }
            events_logic.Events.raise_event(
                'on_access_request',
                **event_kwargs,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                'Access Request Sent.',
            )
            return redirect(
                reverse(
                    'request_submission_access'
                )
            )

    template = 'admin/core/request_submission_access.html'
    context = {
        'check': check,
        'active_request': active_request,
        'form': form,
    }
    return render(
        request,
        template,
        context,
    )


@staff_member_required
def manage_access_requests(request):
    # If we don't have a journal or repository return a 404.
    if not request.journal and not request.repository:
        raise Http404('The Submission Access page is only accessible on Repository and Journal sites.')

    active_requests = models.AccessRequest.objects.filter(
        journal=request.journal,
        repository=request.repository,
        processed=False,
    )
    if request.POST:
        if 'approve' in request.POST:
            pk = request.POST.get('approve')
            access_request = active_requests.get(pk=pk)
            decision = 'approve'

            if request.journal:
                access_request.user.add_account_role(
                    access_request.role.slug,
                    request.journal,
                )
            elif request.repository:
                rm.RepositoryRole.objects.get_or_create(
                    repository=access_request.repository,
                    user=access_request.user,
                    role=access_request.role
                )
        elif 'reject' in request.POST:
            pk = request.POST.get('reject')
            access_request = active_requests.get(pk=pk)
            decision = 'reject'

        if access_request:
            eval_note = request.POST.get('eval_note')
            access_request.evaluation_note = eval_note
            access_request.processed = True
            access_request.save()
            event_kwargs = {
                'decision': decision,
                'access_request': access_request,
                'request': request,
            }
            events_logic.Events.raise_event(
                'on_access_request_complete',
                **event_kwargs,
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                'Access Request Processed.',
            )
        return redirect(
            reverse(
                'manage_access_requests',
            )
        )
    template = 'admin/core/manage_access_requests.html'
    context = {
        'active_requests': active_requests,
    }
    return render(
        request,
        template,
        context,
    )


@method_decorator(staff_member_required, name='dispatch')
class FilteredArticlesListView(generic.ListView):
    model = submission_models.Article
    template_name = 'core/manager/article_list.html'
    paginate_by = '25'
    facets = {}

    # None or integer
    action_queryset_chunk_size = None

    def get_paginate_by(self, queryset):
        paginate_by = self.request.GET.get('paginate_by', self.paginate_by)
        if paginate_by == 'all':
            if queryset:
                paginate_by = len(queryset)
            else:
                paginate_by = self.paginate_by
        return paginate_by

    def get_context_data(self, **kwargs):
        params_querydict = self.request.GET.copy()
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()
        context['paginate_by'] = params_querydict.get('paginate_by', self.paginate_by)
        facets = self.get_facets()

        # Most initial values are in list form
        # The exception is date_time facets
        initial = dict(params_querydict.lists())
        for keyword, value in initial.items():
            if keyword in facets:
                if facets[keyword]['type'] == 'date_time':
                    initial[keyword] = value[0]

        context['facet_form'] = forms.CBVFacetForm(
            queryset=queryset,
            facet_queryset=self.get_facet_queryset(),
            facets=facets,
            initial=initial,
        )

        context['actions'] = self.get_actions()

        params_querydict.pop('action_status', '')
        params_querydict.pop('action_error', '')
        context['params_string'] = params_querydict.urlencode()
        context['version'] = get_janeway_version()
        context['action_maximum_size'] = setting_handler.get_setting(
            'Identifiers',
            'doi_manager_action_maximum_size',
            self.request.journal if self.request.journal else None,
        ).processed_value
        return context

    def get_queryset(self, params_querydict=None):
        if not params_querydict:
            params_querydict = self.request.GET.copy()

        # Clear any previous action status and error
        params_querydict.pop('action_status', '')
        params_querydict.pop('action_error', False)

        self.queryset = super().get_queryset()
        q_stack = []
        facets = self.get_facets()
        for facet in facets.values():
            self.queryset = self.queryset.annotate(**facet.get('annotations', {}))
        for keyword, value_list in params_querydict.lists():
            # The following line prevents the user from passing any parameters
            # other than those specified in the facets.
            if keyword in facets and value_list:
                if value_list[0]:
                    predicates = [(keyword, value) for value in value_list]
                elif facets[keyword]['type'] != 'date_time':
                    if value_list[0] == '' and facets[keyword]['type'] != 'date_time':
                        predicates = [(keyword, '')]
                    else:
                        predicates = [(keyword+'__isnull', True)]
                else:
                    predicates = []
                query = Q()
                for predicate in predicates:
                    query |= Q(predicate)
                q_stack.append(query)
        return self.order_queryset(
            self.filter_queryset_if_journal(
                self.queryset.filter(*q_stack)
            )
        ).exclude(
            stage=submission_models.STAGE_UNSUBMITTED,
        )

    def order_queryset(self, queryset):
        return queryset.order_by('title')

    def get_facets(self):
        facets = {}
        return self.filter_facets_if_journal(facets)

    def get_facet_queryset(self):
        # The default behavior is for the facets to stay the same
        # when a filter is chosen.
        # To make them change dynamically, return None 
        # instead of a separate facet.
        # return None
        queryset = self.filter_queryset_if_journal(
            super().get_queryset()
        ).exclude(
            stage=submission_models.STAGE_UNSUBMITTED
        )
        facets = self.get_facets()
        for facet in facets.values():
            queryset = queryset.annotate(**facet.get('annotations', {}))
        return queryset.order_by()

    def get_actions(self):
        return []

    def post(self, request, *args, **kwargs):

        params_string = request.POST.get('params_string')
        params_querydict = QueryDict(params_string, mutable=True)

        actions = self.get_actions()
        if actions:
            start = time.time()

            action_status = ''
            action_error = False

            querysets = []
            queryset = self.get_queryset(params_querydict=params_querydict)

            if request.journal:
                querysets.extend(self.split_up_queryset_if_needed(queryset))
            else:
                for journal in journal_models.Journal.objects.all():
                    journal_queryset = queryset.filter(journal=journal)
                    if journal_queryset:
                        querysets.extend(self.split_up_queryset_if_needed(journal_queryset))

            for action in actions:
                kwargs = {'start': start}
                if action.get('name') in request.POST:
                    for queryset in querysets:
                        action_status, action_error = action.get('action')(queryset, **kwargs)
                        messages.add_message(
                            request,
                            messages.INFO if not action_error else messages.ERROR,
                            action_status,
                        )

        if params_string:
            return redirect(f'{request.path}?{params_string}')
        else:
            return redirect(request.path)

    def split_up_queryset_if_needed(self, queryset):
        if self.action_queryset_chunk_size:
            n = self.action_queryset_chunk_size
            querysets = [queryset[i:i + n] for i in range(0, queryset.count(), n)]
            return querysets
        else:
            return [queryset]


    def filter_queryset_if_journal(self, queryset):
        if self.request.journal:
            return queryset.filter(journal=self.request.journal)
        else:
            return queryset

    def filter_facets_if_journal(self, facets):
        if self.request.journal:
            facets.pop('journal__pk', '')
            return facets
        else:
            return facets
