from django.contrib import admin

from core.homepage_elements.carousel.models import Carousel, CarouselObject


class CarouselAdmin(admin.ModelAdmin):
    list_display = ('mode', 'exclude',)
    list_filter = ('mode', 'exclude',)
    filter_horizontal = ('articles', 'news_articles',)


admin_list = [
    (Carousel, CarouselAdmin),
    (CarouselObject,),
]

[admin.site.register(*t) for t in admin_list]
