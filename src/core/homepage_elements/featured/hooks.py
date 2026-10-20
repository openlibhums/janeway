from django.utils import timezone

from core.homepage_elements.featured import models
from submission import models as submission_models


def yield_homepage_element_context(request, homepage_elements):
    if (
        homepage_elements is not None
        and homepage_elements.filter(name="Featured Articles").exists()
    ):
        featured_articles = models.FeaturedArticle.objects.filter(
            journal=request.journal,
            article__stage=submission_models.STAGE_PUBLISHED,
            article__date_published__lte=timezone.now(),
        ).select_related("article")

        return {"featured_articles": featured_articles}
    else:
        return {}
