from django.core.exceptions import PermissionDenied

from rest_framework import permissions


class IsEditor(permissions.BasePermission):
    message = 'Checks that the user is an editor for the current journal.'

    def has_permission(self, request, view):

        if request.user and not request.user.is_authenticated():
            raise PermissionDenied

        if request.user.is_editor(request):
            return True
