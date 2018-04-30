import jwt
from datetime import timedelta, datetime
import requests
from requests.auth import HTTPBasicAuth

from django.conf import settings


def create_hypothesis_account(account):
    payload = {
        'authority': settings.HYPOTHESIS_CLIENT_AUTHORITY,
        'username': account.uuid,
        'email': account.email,
        'display_name': account.full_name()
    }

    url = '{base_url}users'.format(base_url=settings.HYPOTHESIS_BASE_URL)

    r = requests.post(url,
                      auth=HTTPBasicAuth(settings.HYPOTHESIS_CLIENT_ID, settings.HYPOTHESIS_CLIENT_SECRET),
                      data=payload)

    if not r.status_code == 200 and settings.DEBUG:
        print('There was an error generating the hypothes.is account for this user. Code {0}.'.format(r.status_code))
    print(url, r.text)


def generate_grant_token(account):
    """
    Generated a hypothesis grant toke for the given user
    :param account: Account object
    :return: jwt encoded token
    """
    now = datetime.utcnow()
    userid = 'acct:{username}@{authority}'.format(username=account.uuid,
                                                  authority=settings.HYPOTHESIS_CLIENT_AUTHORITY)
    payload = {
        'aud': 'hypothes.is',
        'iss': settings.HYPOTHESIS_CLIENT_AUTHORITY_ID,
        'sub': userid,
        'nbf': now,
        'exp': now + timedelta(minutes=10),
    }

    print(payload)

    return jwt.encode(payload, settings.HYPOTHESIS_CLIENT_AUTHORITY_SECRET, algorithm='HS256')