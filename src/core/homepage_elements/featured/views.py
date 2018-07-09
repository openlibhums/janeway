from django.urls import reverse
from django.http import HttpResponse
from django.shortcuts import redirect, render, get_object_or_404
from core.homepage_elements.featured import models
from submission import models as submission_models

from security.decorators import editor_user_required


@editor_user_required
def featured_articles(request):

    featured_arts = models.FeaturedArticle.objects.filter(journal=request.journal)
    featured_article_pks = [f.article.pk for f in featured_arts.all()]
    articles = submission_models.Article.objects.filter(date_published__isnull=False,
                                                        journal=request.journal).exclude(pk__in=featured_article_pks)

    if 'article_id' in request.POST:
        article_id = request.POST.get('article_id')
        article = get_object_or_404(submission_models.Article, pk=article_id, journal=request.journal)

        models.FeaturedArticle.objects.create(
            article=article,
            journal=request.journal,
            added_by=request.user,
            sequence=request.journal.next_featured_article_order()
        )

        return redirect(reverse('featured_articles_setup'))

    if 'delete' in request.POST:
        article_id = request.POST.get('delete')
        featured_article = get_object_or_404(models.FeaturedArticle, article__pk=article_id,
                                             journal=request.journal)
        featured_article.delete()
        return redirect(reverse('featured_articles_setup'))

    template = 'featured_setup.html'
    context = {
        'featured_articles': featured_arts,
        'articles': articles,
    }

    return render(request, template, context)


@editor_user_required
def featured_articles_order(request):
    if request.POST:
        ids = request.POST.getlist('article[]')
        ids = [int(_id) for _id in ids]

        for fa in models.FeaturedArticle.objects.filter(journal=request.journal):
            fa.sequence = ids.index(fa.pk)
            fa.save()

    return HttpResponse('Thanks')
