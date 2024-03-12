from django.contrib import admin

from core.homepage_elements.carousel.models import Carousel


class CarouselAdmin(admin.ModelAdmin):
    list_display = ('mode', 'exclude', 'latest_articles',
                    'latest_news', 'current_issue', 'journal',
                    'press')
    list_filter = ('journal', 'press', 'mode', 'exclude')
    filter_horizontal = ('articles', 'news_articles',)


admin_list = [
    (Carousel, CarouselAdmin),
]

[admin.site.register(*t) for t in admin_list]
