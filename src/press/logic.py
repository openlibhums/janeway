__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from submission import models as submission_models


def get_carousel_items(request):
    if request.press.carousel_type == 'articles':
        carousel_objects = submission_models.Article.objects.all().order_by(
            "-date_published")[:request.press.carousel_items]

        return carousel_objects

    if request.press.carousel_type == 'news':
        news_objects = request.press.carousel_news_items.all()

        return news_objects
