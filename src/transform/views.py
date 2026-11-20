__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect

from core import logic as core_logic
from core import models as core_models
from security.decorators import (
    typesetting_user_or_production_user_or_editor_required,
    has_request,
)

from transform import epub


@login_required
@has_request
@typesetting_user_or_production_user_or_editor_required
def cassius_generate(request, galley_id):
    """Deprecated stub for the removed CaSSius PDF generation feature.

    CaSSius and its pdfkit dependency were removed (#5391), but the URL name
    is retained so that plugins or themes still reversing 'cassius_generate'
    do not fail with NoReverseMatch at render time. This stub can be removed
    in a future release once known references have been updated.
    """
    get_object_or_404(core_models.Galley, pk=galley_id)

    messages.add_message(
        request,
        messages.WARNING,
        "PDF generation with CaSSius has been removed from Janeway.",
    )

    return core_logic.redirect_to_return_url(request)


@login_required
@has_request
@typesetting_user_or_production_user_or_editor_required
def epub_generate(request, galley_id):
    galley = get_object_or_404(core_models.Galley, pk=galley_id)
    epub.generate_ebook_lib_epub(request, galley)

    return redirect(request.GET["return"])
