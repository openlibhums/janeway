__copyright__ = "Copyright 2020 Birkbeck, University of London"
__author__ = "Martin Paul Eve, Andy Byers & Mauro Sanchez"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from django.shortcuts import get_object_or_404

from repository import models


class PreprintRepositoryMiddleware(object):

    @staticmethod
    def process_view(request, view_func, view_args, view_kwargs):
        """
        Checks if repository_short_name is a view_kwarg and adds a repo
        object to request if its present.
        """

        request.repository = None

        if 'repository_short_name' in view_kwargs:
            repository = get_object_or_404(
                models.Repository,
                short_name=view_kwargs.get('repository_short_name'),
                live=True,
            )

            view_kwargs.pop('repository_short_name')
            request.repository = repository


