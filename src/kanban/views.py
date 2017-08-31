__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.db.models import Q
from django.urls import reverse

from submission import models as submission_models
from kanban import logic
from core import models as core_models, files
from security.decorators import editor_user_required

from utils import workflow_tasks
import json
from django.contrib.contenttypes.models import ContentType


@editor_user_required
def home(request):
    template = 'kanban/home.html'

    # group/classify the tasks by their type
    user_tasks = core_models.Task.objects.filter(Q(assignees=request.user) & Q(completed__isnull=True))

    editor_assignment_tasks = []
    reviewer_assignment_tasks = []
    reviewer_request_tasks = []
    reviewer_perform_tasks = []

    for task in user_tasks:
        # we will assume that this is always an article for the safety reasons given in the comment in
        # the task teardown (Core.Models.Task.destroyer)
        article = task.object

        # we need now to determine the stage based on the task title
        if task.title == workflow_tasks.DO_REVIEW_TITLE:
            reviewer_request_tasks.append(task)

        elif task.title == workflow_tasks.PERFORM_REVIEW_TITLE:
            reviewer_perform_tasks.append(task)

        elif task.title == workflow_tasks.ASSIGN_EDITORS_TITLE:
            editor_assignment_tasks.append(task)

        elif task.title == workflow_tasks.SELECT_REVIEWERS_TITLE:
            # TODO: this task needs to be hidden while waiting for author revisions
            # check whether the article already has the number of reviewers required for a section
            active_reviews = task.object.active_reviews
            completed_reviews_with_decision = task.object.completed_reviews_with_decision

            total_reviews = len(active_reviews) + len(completed_reviews_with_decision)

            active_tasks = core_models.Task.objects.filter(
                Q(content_type=ContentType.objects.get_for_model(task.object)) &
                Q(object_id=task.object.pk) & Q(completed__isnull=True))

            if task.object.section.number_of_reviewers > total_reviews:
                # if there are fewer than the minimum number of reviewers assigned, show task
                reviewer_assignment_tasks.append(task)
            else:
                # if any of the reviews themselves are overdue, show task
                done = False

                for review in active_reviews:
                    if review.is_late:
                        done = True
                        reviewer_assignment_tasks.append(task)
                        break

                # if any reviewers have not responded to an overdue review request, show task
                if not done:
                    for related_task in active_tasks:
                        if related_task.is_late and related_task != task:
                            done = True
                            reviewer_assignment_tasks.append(task)
                            break

                # if the minimum number of reviews for this article are complete, show task
                if not done:
                    if len(completed_reviews_with_decision) >= task.object.section.number_of_reviewers:
                        done = True
                        reviewer_assignment_tasks.append(task)

    context = {
        'tasks': core_models.Task.objects.filter(assignees=request.user),
        'editor_assignment_tasks': editor_assignment_tasks,
        'reviewer_assignment_tasks': reviewer_assignment_tasks,
        'reviewer_request_tasks': reviewer_request_tasks,
        'reviewer_perform_tasks': reviewer_perform_tasks
    }

    return render(request, template, context)


@editor_user_required
def new_note(request, article_id):
    article = get_object_or_404(submission_models.Article, pk=article_id)

    if request.POST:

        note = request.POST.get('note')

        sav_note = submission_models.Note.objects.create(
            article=article,
            creator=request.user,
            text=note,
        )

        return_dict = {'id': sav_note.pk, 'note': sav_note.text, 'initials': sav_note.creator.initials(),
                       'date_time': str(sav_note.date_time),
                       'html': logic.create_html_snippet(sav_note)}

    else:

        return_dict = {'error': 'This request must be made with POST'}

    return HttpResponse(json.dumps(return_dict), content_type="application/json")


@editor_user_required
def delete_note(request, article_id, note_id):
    note = get_object_or_404(submission_models.Note, pk=note_id)
    note.delete()

    url = reverse('kanban_home')

    return redirect("{0}?article_id={1}".format(url, article_id))


@editor_user_required
def serve_article_file(request, article_id, file_id):
    article = get_object_or_404(submission_models.Article, pk=article_id)
    file = get_object_or_404(core_models.File, pk=file_id)

    response = files.serve_file(request, file, article)
    return response
