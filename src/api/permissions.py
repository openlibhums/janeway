from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from rest_framework import permissions

from repository import models as rm


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


class IsRepositoryManager(permissions.BasePermission):
    message = 'Please ensure the user is a manager of this repository.'

    def has_permission(self, request, view):
        if request.user and not request.user.is_authenticated:
            return False

        if not request.repository:
            return False

        if request.user.is_staff:
            return True

        if request.repository and request.user in request.repository.managers.all():
            return True


class IsPreprintOwner(permissions.BasePermission):
    message = 'You must be the owner of this preprint to edit it.'

    def has_permission(self, request, view):
        # grant access to non-create/update requests
        if request.method not in ['PUT', 'PATCH']:
            return True

        # grant access if user is the preprint's owner
        preprint_id = request.data.get('pk')
        if not preprint_id:
            preprint_id = view.kwargs.get('pk')

        preprint = get_object_or_404(
            rm.Preprint,
            pk=preprint_id,
        )
        if request.user == preprint.owner:
            return True

        if request.user.is_staff:
            return True

        # Otherwise don't grant access
        return False