from django.core.exceptions import PermissionDenied

from rest_framework import permissions


class IsEditor(permissions.BasePermission):
    message = 'Please ensure the user is an Editor or Staff Member.'

    def has_permission(self, request, view):
        if request.user and not request.user.is_authenticated:
            raise PermissionDenied

        if request.user.is_staff:
            return True

        if request.user.is_editor(request):
            return True


class IsSectionEditor(permissions.BasePermission):
    message = 'Please ensure the user is a Section Editor or Staff Member.'

    def has_permission(self, request, view):
        if request.user and not request.user.is_authenticated:
            raise PermissionDenied

        if request.user.is_staff:
            return True

        if request.user.is_section_editor(request):
            return True
