__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"


import json
import requests
from urllib.parse import urlencode
from django.conf import settings


def retrieve_tokens(authorization_code, domain=None):
    access_token_req = {
        "code": authorization_code,
        "client_id": settings.ORCID_CLIENT_ID,
        "client_secret": settings.ORCID_CLIENT_SECRET,
        "redirect_uri": '%s/login/orcid/' % domain if domain else settings.ORCID_REDIRECT_URI,
        "grant_type": "authorization_code",
    }

    content_length = len(urlencode(access_token_req))
    access_token_req['content-length'] = str(content_length)
    base_url = settings.ORCID_TOKEN_URL

    r = requests.post(base_url, data=access_token_req)
    data = json.loads(r.text)

    return data
