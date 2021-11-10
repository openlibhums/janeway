from django.contrib import admin

from core.homepage_elements.carousel.models import Carousel, CarouselObject


class CarouselAdmin(admin.ModelAdmin):
    list_display = ('exclude', 'latest_articles', 'latest_news', 'current_issue')
    list_filter = ('exclude','journal')
    filter_horizontal = ('articles', 'news_articles',)


admin_list = [
    (Carousel, CarouselAdmin),
    (CarouselObject,),
]

[admin.site.register(*t) for t in admin_list]
