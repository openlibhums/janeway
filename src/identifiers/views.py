__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


from django.http import HttpResponse

from utils import models as util_models


def pingback(request):
    # TODO: not sure what Crossref will actually send here so for now it just dumps all data

    output = ''

    for key, value in request.POST.items():
        output += '{0}: {1}\n'.format(key, value)

    util_models.LogEntry.add_entry('Submission', "Response from Crossref pingback: {0}".format(output), 'Info')

    return HttpResponse('')
