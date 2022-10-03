__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.utils import timezone

from utils import notify, render_template
from submission import models as submission_models
from review import models as review_models
from proofing import models as proofing_models


def task_runner(task):
    if task.task_type == 'slack_message':
        pass
    elif task.task_type == 'email_message':
        log_dict = {'level': 'Info', 'action_text': task.task_data, 'types': task.task_type,
                    'target': task.article}
        notify.notification(**{'action': ['email'], 'task': task, 'log_dict': log_dict})


def process_editor_digest(journal, user_role):
    unassigned_articles = submission_models.Article.objects.filter(stage=submission_models.STAGE_UNASSIGNED,
                                                                   journal=journal)
    overdue_reviews = review_models.ReviewAssignment.objects.filter(date_complete__isnull=False,
                                                                    date_declined__isnull=True,
                                                                    is_complete=False,
                                                                    date_due__lte=timezone.now(),
                                                                    article__journal=journal)
    overdue_revisions = review_models.RevisionRequest.objects.filter(date_completed__isnull=True,
                                                                     date_due__lte=timezone.now(),
                                                                     article__journal=journal)
    overdue_proofing = proofing_models.ProofingTask.objects.filter(completed__isnull=True,
                                                                   cancelled__isnull=True,
                                                                   due__lte=timezone.now(),
                                                                   round__assignment__article__journal=journal)
    awaiting_publication = submission_models.Article.objects.filter(stage=submission_models.STAGE_READY_FOR_PUBLICATION,
                                                                    journal=journal)

    context = {
        'unassigned_articles': unassigned_articles,
        'overdue_reviews': overdue_reviews,
        'overdue_revisions': overdue_revisions,
        'overdue_proofing': overdue_proofing,
        'awaiting_publication': awaiting_publication,
    }

    return render_template.get_requestless_content(context, journal, 'editor_digest')


def process_revision_digest(journal, user_role):
    pending_requests = review_models.RevisionRequest.objects.filter(article__correspondence_author=user_role.user,
                                                                    date_completed__isnull=True,
                                                                    date_due__gte=timezone.now())
    overdue_requests = review_models.RevisionRequest.objects.filter(article__correspondence_author=user_role.user,
                                                                    date_completed__isnull=True,
                                                                    date_due__lte=timezone.now())

    context = {
        'pending_requests': pending_requests,
        'overdue_requests': overdue_requests,
    }

    return render_template.get_requestless_content(context, journal, 'revision_digest')


def process_reviewer_digest(journal, user_role):
    pending_requests = review_models.ReviewAssignment.objects.filter(reviewer=user_role.user,
                                                                     date_complete__isnull=True,
                                                                     date_due__gte=timezone.now())
    overdue_requests = review_models.ReviewAssignment.objects.filter(reviewer=user_role.user,
                                                                     date_complete__isnull=True,
                                                                     date_due__lte=timezone.now())

    context = {
        'pending_requests': pending_requests,
        'overdue_requests': overdue_requests,
    }
    return render_template.get_requestless_content(context, journal, 'reviewer_digest')


def process_digest_items(journal, user_role):
    text = None
    if user_role.role.slug == 'editor':
        text = process_editor_digest(journal, user_role)
    elif user_role.role.slug == 'author':
        text = process_revision_digest(journal, user_role)
    elif user_role.role.slug == 'reviewer':
        text = process_reviewer_digest(journal, user_role)

    return text


def check_template_exists(request, reminder):
    try:
        request.journal.get_setting('email', reminder.template_name)
        return True
    except BaseException:
        return False
