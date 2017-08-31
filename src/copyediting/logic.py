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
    copyeditor_assignments = models.CopyeditAssignment.objects.filter(article=article)
    copyeditors = [assignment.copyeditor.pk for assignment in copyeditor_assignments]

    return core_models.AccountRole.objects.filter(role__slug='copyeditor').exclude(user__pk__in=copyeditors)


def get_user_from_post(post):
    user_id = post.get('copyeditor')

    if user_id:
        user = core_models.Account.objects.get(pk=user_id)
        return user
    else:
        return None


def get_copyeditor_notification(request, article, copyedit):

    email_context = {
        'article': article,
        'assignment': copyedit,
    }

    return render_template.get_message_content(request, email_context, 'copyeditor_assignment_notification')


def get_copyedit_message(request, article, copyedit, template):

    email_context = {
        'article': article,
        'assignment': copyedit,
    }

    return render_template.get_message_content(request, email_context, template)


def handle_file_post(request, copyedit):
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


def request_author_review(copyedit, article, request):
    user_message_content = request.POST.get('review_note')

    author_review = models.AuthorReview.objects.create(
        author=article.correspondence_author,
        assignment=copyedit,
        notified=True
    )

    url = reverse('author_copyedit', kwargs={'article_id': article.pk, 'author_review_id': author_review.pk})

    kwargs = {
        'copyedit_assignment': copyedit,
        'article': article,
        'user_message_content': user_message_content,
        'request': request,
        'skip': True if 'skip' in request.POST else False,
        'url': url,
    }

    event_logic.Events.raise_event(event_logic.Events.ON_COPYEDIT_AUTHOR_REVIEW, **kwargs)

    return author_review


def accept_copyedit(copyedit, article, request):
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
