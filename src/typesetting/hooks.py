from django.template.loader import render_to_string

from plugins.typesetting import models


def author_tasks(context):
    request = context['request']
    article = context['article']

    author_proofing_tasks = models.GalleyProofing.objects.filter(
        round__article=article,
        round__article__authors=request.user,
        proofreader=request.user,
        completed__isnull=True,
        cancelled=False,
    )

    if author_proofing_tasks.exists():

        return render_to_string(
            'typesetting/elements/author_tasks.html',
            {
                'article': article,
                'author_proofing_tasks': author_proofing_tasks,
            },
        )

    return ''
