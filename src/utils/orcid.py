__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json
from urllib.parse import urlencode

from django.conf import settings
from django.urls import reverse
import requests
from requests.exceptions import HTTPError

from utils import logic
from utils.logger import get_logger
from orcid import PublicAPI as OrcidAPI

logger = get_logger(__name__)


def retrieve_tokens(authorization_code, site):
    """ Retrieves the access token for the given code

    :param authorization_code: (str) code provided by ORCID
    :site: Object implementing the AbstractSiteModel interface
    :return: ORCID ID or None
    """
    redirect_uri = build_redirect_uri(site)
    access_token_req = {
        "code": authorization_code,
        "client_id": settings.ORCID_CLIENT_ID,
        "client_secret": settings.ORCID_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    content_length = len(urlencode(access_token_req))
    access_token_req['content-length'] = str(content_length)
    base_url = settings.ORCID_TOKEN_URL

    logger.info("Connecting with ORCID on %s" % base_url)
    r = requests.post(base_url, data=access_token_req)
    try:
        r.raise_for_status()
    except HTTPError as e:
        logger.error("ORCID request failed: %s" % str(e))
        orcid_id = None
    else:
        logger.info("OK response from ORCID")
        orcid_id = json.loads(r.text).get("orcid")

    return orcid_id


def build_redirect_uri(site):
    """ builds the landing page for ORCID requests
    :site: Object implementing the AbstractSiteModel interface
    :return: (str) Redirect URI for ORCID requests
    """
    request = logic.get_current_request()
    path = reverse("core_login_orcid")

    return request.site_type.site_url(path)


def get_orcid_record_details(orcid):
    details = {}
    try:
        logger.info("Retrieving ORCiD profile for %s", orcid)
        api_client = OrcidAPI(
            settings.ORCID_CLIENT_ID,
            settings.ORCID_CLIENT_SECRET,
        )
        search_token = api_client.get_search_token_from_orcid()
        record = api_client.read_record_public(
            orcid, 'record', search_token,
        )
        if record:
            user_record = record["person"]
            # Order matters here, we want to get emails first in case anything
            # goes wrong with person details below
            details["emails"] = [
                email["email"]
                for email in user_record["emails"]["email"]
            ]
            details["last_name"] = user_record["name"]["family-name"]["value"]
            details["first_name"] = user_record["name"]["given-names"]["value"]
    except HTTPError as e:
        logger.info("Couldn't retrieve profile with ORCID %s", orcid)
        logger.info(e)
    except Exception as e:
        logger.error("Failed to retrieve user details from ORCID API: %s")
        logger.exception(e)

    return details
