__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from django.urls import reverse

from core import models
from events import logic as event_logic


ASSIGN_EDITORS_TITLE = 'New manuscript requires assignment'
SELECT_REVIEWERS_TITLE = 'Manuscript requires reviewers'
DO_REVIEW_TITLE = 'Review Request'
PERFORM_REVIEW_TITLE = 'Peer Review'


def assign_editors(**kwargs):
    article = kwargs.get('article')

    task_dict = {
        'object': article,
        'title': ASSIGN_EDITORS_TITLE,
        'description': 'An article has been submitted. You must now assign an editor to handle it.',
        'link': reverse('review_unassigned_article', kwargs={'article_id': article.id}),
        'due': article.date_submitted
    }

    task = models.Task.objects.create(**task_dict)

    # add teardown events

    # when the article is assigned
    on_article_assigned, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_ARTICLE_ASSIGNED)
    task.complete_events.add(on_article_assigned.pk)

    # when the article is re-submitted (to avoid duplicate tasks)
    on_article_submitted, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_ARTICLE_SUBMITTED)
    task.complete_events.add(on_article_submitted.pk)

    # when the article is rejected
    on_article_declined, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_ARTICLE_DECLINED)
    task.complete_events.add(on_article_declined.pk)

    # when the article is accepted
    on_article_accepted, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_ARTICLE_ACCEPTED)
    task.complete_events.add(on_article_accepted.pk)

    all_editors = models.AccountRole.objects.filter(role__slug='editor')

    for editor in all_editors:
        task.assignees.add(editor.user)

    task.save()


# TODO: we need a "move to review" task for when editors have been assigned
def select_reviewers(**kwargs):
    assignment = kwargs.get('editor_assignment')
    article = assignment.article

    task_dict = {
        'object': article,
        'title': SELECT_REVIEWERS_TITLE,
        'description': 'You have been assigned as an article editor. Please initiate the review process.',
        'link': reverse('review_in_review', kwargs={'article_id': article.id}),
        'due': article.date_submitted
    }

    task = models.Task.objects.create(**task_dict)

    # add teardown events

    # when the article is rejected
    on_article_declined, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_ARTICLE_DECLINED)
    task.complete_events.add(on_article_declined.pk)

    # when the article is accepted
    on_article_accepted, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_ARTICLE_ACCEPTED)
    task.complete_events.add(on_article_accepted.pk)

    all_editors = models.AccountRole.objects.filter(role__slug='editor')

    for editor in all_editors:
        task.assignees.add(editor.user)

    task.save()


def do_review_task(**kwargs):
    review_assignment = kwargs.get('review_assignment')

    task_dict = {
        'object': review_assignment.article,
        'title': DO_REVIEW_TITLE,
        'description': 'You have been asked to complete a review of this article, please let the Editor know if you '
                       'are able to do so.',
        'link': reverse('review_requests'),
        'due': review_assignment.date_due
    }

    task = models.Task.objects.create(**task_dict)

    # add teardown events

    # when the review is accepted
    on_accepted, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_REVIEWER_ACCEPTED)
    task.complete_events.add(on_accepted.pk)

    # when the review is declined
    on_declined, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_REVIEWER_DECLINED)
    task.complete_events.add(on_declined.pk)

    # when the review is closed
    on_review_closed, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_REVIEW_CLOSED)
    task.complete_events.add(on_review_closed.pk)

    task.assignees.add(review_assignment.reviewer)
    task.save()


def perform_review_task(**kwargs):
    review_assignment = kwargs.get('review_assignment')

    task_dict = {
        'object': review_assignment.article,
        'title': PERFORM_REVIEW_TITLE,
        'description': 'You have been asked to complete a review of this article, please download the relevant files '
                       'and submit your decision to the editor.',
        'link': reverse('do_review', kwargs={'assignment_id': review_assignment.id}),
        'due': review_assignment.date_due
    }

    task = models.Task.objects.create(**task_dict)

    # add teardown events

    # when the reviewer completes his or her review
    on_review_complete, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_REVIEW_COMPLETE)
    task.complete_events.add(on_review_complete.pk)

    # when the review is closed
    on_review_closed, created = models.TaskCompleteEvents.objects.get_or_create(
        event_name=event_logic.Events.ON_REVIEW_CLOSED)
    task.complete_events.add(on_review_closed.pk)

    task.assignees.add(review_assignment.reviewer)
    task.save()


def create_copyedit_task(**kwargs):
    # stubby mcstub face
    pass
