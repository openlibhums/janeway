__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.utils import timezone
from django.contrib import messages
from django.http import Http404
from django.urls import reverse

from copyediting import models
from core import models as core_models, files
from utils import render_template
from events import logic as event_logic


def get_copyeditors(article):
    """
    Gets a list of copyeditors that haven't already been assigned to the article.
    :param article: a Article object
    :return: a queryset of AccountRole objects
    """
    copyeditor_assignments = models.CopyeditAssignment.objects.filter(article=article)
    copyeditors = [assignment.copyeditor.pk for assignment in copyeditor_assignments]

    return core_models.AccountRole.objects.filter(role__slug='copyeditor',
                                                  journal=article.journal).exclude(user__pk__in=copyeditors)


def get_user_from_post(request):
    """
    Grabs a string from POST and fetches the related user, returns None if no user_id is found.
    :param post: request.POST object
    :return: a Account object or None
    """
    user_id = request.POST.get('copyeditor')

    if user_id:
        user = core_models.Account.objects.get(pk=user_id)

        if not user.is_copyeditor(request):
            return None

        return user
    else:
        return None


def get_copyeditor_notification(request, article, copyedit):
    """
    Takes a set of variables and renders a template into a string.
    :param request: HttpRequest object
    :param article: Article object
    :param copyedit: CopyeditAssignment Object
    :return: a template rendered into a string
    """
    copyedit_requests_url = request.journal.site_url(
        reverse("copyedit_requests"))
    email_context = {
        'article': article,
        'assignment': copyedit,
        'copyedit_requests_url': copyedit_requests_url,
    }

    return render_template.get_message_content(request, email_context, 'copyeditor_assignment_notification')


def get_copyedit_message(request, article, copyedit, template,
                         author_review=None):
    """
    Takes a set of variables and renders a template into a string.
    :param request: HttpReqest object
    :param article: Article object
    :param copyedit: CopyeditAssignment object
    :param template: a string matching a Setting.name from the email
    setting group
    :param author_review: an AuthorReview object relating to the
    CopyeditAssignment
    :return:
    """
    if author_review:
        copyedit_review_url = request.journal.site_url(path=reverse(
            'author_copyedit', args=[article.pk, author_review.pk]))
    else:
        copyedit_review_url = None

    copyedit_requests_url = request.journal.site_url(path=reverse(
        'copyedit_requests'))

    email_context = {
        'article': article,
        'assignment': copyedit,
        'author_review': author_review,
        'author_copyedit_url': copyedit_review_url,
        'copyedit_requests_url': copyedit_requests_url,
    }

    return render_template.get_message_content(request, email_context, template)


def handle_file_post(request, copyedit):
    """
    Handles uploading of copyediting files, checks a file has been selected and a label has been entered, Assigs the
    file to the CopyeditAssignment.
    :param request: HttpRequest
    :param copyedit: CopyeditAssignment object
    :return: None or a list of errors
    """
    errors = []
    file = request.FILES.get('file')
    file_label = request.POST.get('label')

    if not file:
        errors.append('You must select a file.')
    if not file_label:
        errors.append('You must add a label for your file.')

    if not errors:
        new_file = files.save_file_to_article(file, copyedit.article, request.user, label=file_label)
        copyedit.copyeditor_files.add(new_file)
        return None
    else:
        return errors


def request_author_review(request, article, copyedit, author_review):
    """
    :param request:
    :param article:
    :param copyedit:
    :param author_review:
    :return:
    """
    user_message_content = request.POST.get('content_email')

    kwargs = {
        'copyedit_assignment': copyedit,
        'article': article,
        'author_review': author_review,
        'user_message_content': user_message_content,
        'request': request,
        'skip': True if 'skip' in request.POST else False,
    }

    event_logic.Events.raise_event(
        event_logic.Events.ON_COPYEDIT_AUTHOR_REVIEW, **kwargs)


def accept_copyedit(copyedit, article, request):
    """
    Raises an event when a copyedit is accepted
    :param copyedit: CopyeditAssignment object
    :param article: Article object
    :param request: HttpRequest object
    :return: None
    """
    user_message_content = request.POST.get('accept_note')

    kwargs = {
        'copyedit_assignment': copyedit,
        'article': article,
        'user_message_content': user_message_content,
        'request': request,
        'skip': True if 'skip' in request.POST else False
    }

    event_logic.Events.raise_event(event_logic.Events.ON_COPYEDIT_ACKNOWLEDGE, **kwargs)

    copyedit.copyedit_accepted = timezone.now()

    if 'skip' not in request.POST:
        copyedit.copyedit_acknowledged = True

    copyedit.save()


def reset_copyedit(copyedit, article, request):
    user_message_content = request.POST.get('reset_note')
    due = request.POST.get('due')

    copyedit.copyedit_reopened = timezone.now()
    copyedit.copyedit_reopened_complete = None
    copyedit.due = due
    copyedit.save()

    kwargs = {
        'copyedit_assignment': copyedit,
        'article': article,
        'user_message_content': user_message_content,
        'request': request,
        'skip': True if 'skip' in request.POST else False
    }

    event_logic.Events.raise_event(event_logic.Events.ON_COPYEDIT_REOPEN, **kwargs)


def attempt_to_serve_file(request, copyedit):
    if request.GET.get('file_id', None):
        file_id = request.GET.get('file_id')
        _type = request.GET.get('type', None)
        try:
            if _type == 'for_copyedit':
                file = copyedit.files_for_copyediting.get(pk=file_id)
            else:
                file = copyedit.copyeditor_files.get(pk=file_id)
            return files.serve_file(request, file, copyedit.article)
        except core_models.File.DoesNotExist:
            messages.add_message(request, messages.WARNING, 'File does not exist.')

        raise Http404
