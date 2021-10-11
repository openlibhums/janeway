from django.core.exceptions import PermissionDenied

from rest_framework import permissions


class IsEditor(permissions.BasePermission):
    message = 'Please ensure the user is an Editor or Staff Member.'

    def has_permission(self, request, view):

        if request.user and not request.user.is_authenticated():
            raise PermissionDenied

        if request.user.is_editor(request) or request.user.is_staff:
            return True
