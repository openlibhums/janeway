__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import os

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from core import models as core_models
from security.decorators import typesetting_user_or_production_user_or_editor_required, has_request
from transform.logic import CassiusDriver

from transform import epub


@login_required
@has_request
@typesetting_user_or_production_user_or_editor_required
def cassius_generate(request, galley_id):

    galley = get_object_or_404(core_models.Galley, pk=galley_id)

    temporary_directory = os.path.join(settings.BASE_DIR, 'files', 'temp')

    driver = CassiusDriver(temporary_directory, galley, request)
    driver.transform()

    return redirect(request.GET['return'])


@login_required
@has_request
@typesetting_user_or_production_user_or_editor_required
def epub_generate(request, galley_id):

    galley = get_object_or_404(core_models.Galley, pk=galley_id)
    epub.generate_ebook_lib_epub(request, galley)

    return redirect(request.GET['return'])
