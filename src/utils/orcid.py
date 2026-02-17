__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import json
import re
from urllib.parse import quote, unquote, urlencode, urlparse

from collections import defaultdict
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import QueryDict
import requests
from requests.exceptions import HTTPError
import datetime

from utils import logic
from utils.logger import get_logger
from orcid import PublicAPI as OrcidAPI

logger = get_logger(__name__)


def retrieve_tokens(authorization_code, site):
    """Retrieves the access token for the given code

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
    access_token_req["content-length"] = str(content_length)
    base_url = settings.ORCID_TOKEN_URL

    logger.info("Connecting with ORCID on %s" % base_url)
    r = requests.post(base_url, data=access_token_req)
    try:
        r.raise_for_status()
    except HTTPError as e:
        logger.error("ORCID request failed: %s" % str(e))
        # after logging failure continue with an empty response
        # to avoid additional errors
        orcid_response = {}
    else:
        logger.info("OK response from ORCID")
        orcid_response = json.loads(r.text)

    access_token = orcid_response.get("access_token", None)
    orcid_id = orcid_response.get("orcid", None)

    if "expires_in" in orcid_response:
        expires = orcid_response.get("expires_in")
        expiration_date = datetime.datetime.now() + datetime.timedelta(seconds=expires)
    else:
        expiration_date = None

    return access_token, expiration_date, orcid_id


def is_token_valid(orcid_id, token):
    api_client = OrcidAPI(
        settings.ORCID_CLIENT_ID,
        settings.ORCID_CLIENT_SECRET
    )
    r = api_client._get_public_info(
        orcid_id, "record", token, None, "application/orcid+json"
    )
    return r.status_code == 200


def revoke_token(token):
    url = settings.ORCID_TOKEN_URL.replace("token", "revoke")
    data = {
        "client_id": settings.ORCID_CLIENT_ID,
        "client_secret": settings.ORCID_CLIENT_SECRET,
        "token": token,
    }
    r = requests.post(url, data=data)
    return r.status_code == 200


def build_redirect_uri(site):
    """builds the landing page for ORCID requests
    :site: Object implementing the AbstractSiteModel interface
    :return: (str) Redirect URI for ORCID requests
    """
    return site.site_url(reverse("core_login_orcid"))


def get_orcid_record(orcid):
    try:
        logger.info("Retrieving ORCID profile for %s", orcid)
        api_client = OrcidAPI(
            settings.ORCID_CLIENT_ID,
            settings.ORCID_CLIENT_SECRET
        )
        search_token = api_client.get_search_token_from_orcid()
        return api_client.read_record_public(
            orcid,
            "record",
            search_token,
        )
    except HTTPError as e:
        logger.info("Couldn't retrieve profile with ORCID %s", orcid)
        logger.info(e)
    except Exception as e:
        logger.error("Failed to retrieve user details from ORCID API: %s")
        logger.exception(e)

    return None


def get_affiliation(summary):
    raise DeprecationWarning("Use get_affiliations instead.")
    if len(summary["employments"]["employment-summary"]):
        return summary["employments"]["employment-summary"][0]["organization"]
    elif len(summary["educations"]["education-summary"]):
        return summary["educations"]["education-summary"][0]["organization"]
    else:
        return None


def get_affiliations(summary):
    affils = []
    affils.extend([affil for affil in summary["employments"]["employment-summary"]])
    if not affils:
        affils.extend([affil for affil in summary["educations"]["education-summary"]])
    return affils


def get_orcid_record_details(orcid):
    details = defaultdict(lambda: None)
    record = get_orcid_record(orcid)
    if record:
        details["uri"] = record["orcid-identifier"]["uri"]
        details["orcid"] = record["orcid-identifier"]["path"]
        user_record = record["person"]
        # Order matters here, we want to get emails first in case anything
        # goes wrong with person details below
        details["emails"] = [email["email"] for email in user_record["emails"]["email"]]

        name = user_record.get("name", None)
        if name:
            if name.get("family-name", None):
                details["last_name"] = name["family-name"]["value"]
            if name.get("given-names", None):
                details["first_name"] = name["given-names"]["value"]

        affiliations = get_affiliations(record["activities-summary"])
        if affiliations:
            details["affiliations"] = affiliations
            details["affiliation"] = affiliations[0]["organization"]["name"]
            details["country"] = affiliations[0]["organization"]["address"]["country"]

    return details


def encode_state(next_url, orcid_action):
    """
    Encode information related to Janeway application state in a form that can
    be sent and received back from ORCiD authentication, independently
    of the redirect URI, which the ORCiD auth system must be able to predict.
    See https://info.orcid.org/documentation/integration-guide/customizing-the-sign-in-register-screen/#h-identify-the-researcher-by-a-custom-state-parameter

    :param next_url: a raw URL (can include its own query parameters)
    :param orcid_action: 'login' or 'register'
    :return: a query string with percent-encoded paramater values
        that can be passed to ORCiD in a URL as a callback
    """
    querydict = QueryDict(mutable=True)
    if next_url:
        querydict["next"] = next_url
    if orcid_action:
        querydict["action"] = orcid_action
    encoded_state = querydict.urlencode(safe="/")
    return encoded_state


def decode_state(encoded_state):
    """
    :param encoded_state: a percent-encoded query string value
        like next=a&action=b
    :return: a QueryDict with entries for next_url and action
        like {'next':'a','action':'b'}
    """
    return QueryDict(encoded_state)


COMPILED_ORCID_REGEX = re.compile(
    r"([0]{3})([0,9]{1})-([0-9]{4})-([0-9]{4})-([0-9]{3})([0-9X]{1})"
)


def validate_orcid(orcid):
    if not COMPILED_ORCID_REGEX.match(orcid):
        raise ValidationError(f"{orcid} is not a valid ORCID")
