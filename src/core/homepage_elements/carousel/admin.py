from django.contrib import admin

from core.homepage_elements.carousel.models import Carousel, CarouselObject

admin_list = [
    (Carousel,),
    (CarouselObject,),
]

[admin.site.register(*t) for t in admin_list]
