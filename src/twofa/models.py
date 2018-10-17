from django.db import models

two_factor_types = (
    ('email', 'Email'),
    ('u2f', 'U2F'),
    ('authenticator', 'Authenticator')
)


class UserRegistration(models.Model):
    account = models.ForeignKey('core.Account')
    type = models.CharField(max_length=10, choices=two_factor_types)


class Code(models.Model):
    account = models.ForeignKey('core.Account')
    code = models.TextField()
    active_until = models.DateTimeField()
