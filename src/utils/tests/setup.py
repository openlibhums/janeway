__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

from core import models as core_models
from journal import models as journal_models
from press import models as press_models


def create_user(username, roles=None, journal=None):
    """
    Creates a user with the specified permissions.
    :return: a user with the specified permissions
    """
    # check this way to avoid mutable default argument
    if roles is None:
        roles = []

    kwargs = {'username': username}
    user = core_models.Account.objects.create_user(email=username, **kwargs)

    for role in roles:
        resolved_role = core_models.Role.objects.get(name=role)
        core_models.AccountRole(user=user, role=resolved_role, journal=journal).save()

    user.save()

    return user


def create_roles(roles=None):
    """
    Creates the necessary roles for testing.
    :return: None
    """
    # check this way to avoid mutable default argument
    if roles is None:
        roles = []

    for role in roles:
        core_models.Role(name=role, slug=role).save()


def create_journals():
    """
    Creates a set of dummy journals for testing
    :return: a 2-tuple of two journals
    """
    journal_one = journal_models.Journal(code="TST", domain="testserver")
    journal_one.save()

    journal_two = journal_models.Journal(code="TSA", domain="journal2.localhost")
    journal_two.save()

    return journal_one, journal_two


def create_press():
    return press_models.Press.objects.create(name='Press', domain='localhost', main_contact='a@b.com')
