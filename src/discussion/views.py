from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.http import Http404
from django.views.decorators.http import require_POST

from discussion import models, forms
from submission import models as submission_models
from repository import models as repository_models
from security.decorators import editor_or_manager


@editor_or_manager
def threads(request, object_type, object_id, thread_id=None):
    """
    Grabs threads for an object type.
    """
    modal = None

    if object_type == 'article':
        object_to_get = get_object_or_404(
            submission_models.Article,
            pk=object_id,
            journal=request.journal,
        )
        threads = models.Thread.objects.filter(
            article=object_to_get,
        )
    else:
        object_to_get = get_object_or_404(
            repository_models.Preprint,
            pk=object_id,
            repository=request.repository,
        )
        threads = models.Thread.objects.filter(
            preprint=object_to_get,
        )

    if thread_id:
        try:
            thread = threads.get(
                pk=thread_id,
            )
        except models.Thread.DoesNotExist:
            raise Http404
    else:
        thread = None

    template = 'admin/discussion/threads.html'
    context = {
        'object': object_to_get,
        'object_type': object_type,
        'threads': threads,
        'active_thread': thread,
        'modal': modal,
    }
    return render(request, template, context)


@editor_or_manager
def manage_thread(request, object_type, object_id, thread_id=None):
    thread = None
    if thread_id:
        thread = get_object_or_404(
            models.Thread,
            pk=thread_id,
        )
    if object_type == 'article':
        object_to_get = get_object_or_404(
            submission_models.Article,
            pk=object_id,
            journal=request.journal,
        )
    else:
        object_to_get = get_object_or_404(
            repository_models.Preprint,
            pk=object_id,
            repository=request.repository,
        )

    form = forms.ThreadForm(
        object=object_to_get,
        object_type=object_type,
        owner=request.user,
    )

    if request.POST:
        form = forms.ThreadForm(
            request.POST,
            object=object_to_get,
            object_type=object_type,
            owner=request.user,
        )
        if form.is_valid():
            thread = form.save()
            return redirect(
                reverse(
                    'discussion_thread',
                    kwargs={
                        'object_type': thread.object_string(),
                        'object_id': thread.object_id(),
                        'thread_id': thread.pk,
                    }
                )
            )
    template = 'admin/discussion/manage_thread.html'
    context = {
        'object': object_to_get,
        'object_type': object_type,
        'form': form,
    }
    return render(request, template, context)


def user_threads(request, object_type, object_id, thread_id=None):
    """
    Grabs threads for an object type.
    """
    modal = None
    print(object_type, object_id, thread_id)

    if object_type == 'article':
        object_to_get = get_object_or_404(
            submission_models.Article,
            pk=object_id,
            journal=request.journal,
        )
        threads = models.Thread.objects.filter(
            article=object_to_get,
            posters=request.user,
        )
    else:
        object_to_get = get_object_or_404(
            repository_models.Preprint,
            pk=object_id,
            repository=request.repository,
        )
        threads = models.Thread.objects.filter(
            preprint=object_to_get,
            posters=request.user,
        )

    if thread_id:
        try:
            thread = threads.get(
                pk=thread_id,
                posters=request.user
            )
        except models.Thread.DoesNotExist:
            print('Here')
            raise Http404('We could not find that thread.')
    else:
        thread = None

    template = 'admin/discussion/user_threads.html'
    context = {
        'object': object_to_get,
        'object_type': object_type,
        'threads': threads,
        'active_thread': thread,
        'modal': modal,
    }
    return render(request, template, context)


@require_POST
@editor_or_manager
def add_post(request, thread_id):
    thread = get_object_or_404(
        models.Thread,
        pk=thread_id,
    )
    thread.create_post(
        request.user,
        request.POST.get('new_post'),
    )
    reverse_url_name = 'discussion_thread'
    if request.POST.get('user'):
        reverse_url_name = 'user_discussion_thread'

    print(reverse_url_name)

    return redirect(
        reverse(
            reverse_url_name,
            kwargs={
                'object_type': thread.object_string(),
                'object_id': thread.object_id(),
                'thread_id': thread.pk,
            }
        )
    )


