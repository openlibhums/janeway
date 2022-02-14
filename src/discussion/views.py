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
            thread = threads.get(pk=thread_id)
        except models.Thread.DoesNotExist:
            raise Http404
    else:
        thread = None

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
        else:
            modal = 'new_thread'

    template = 'admin/discussion/threads.html'
    context = {
        'object': object_to_get,
        'object_type': object_type,
        'threads': threads,
        'active_thread': thread,
        'form': form,
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


