__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import random
import mimetypes
from datetime import datetime
from urllib.parse import urlencode, quote_plus

from django.core.cache import cache
from django.utils import timezone
from django.shortcuts import reverse, redirect

# NB: this module should not import any others in the application.
# It is a space for communal functions to avoid
# circular imports and to thereby maintain Python 3.4 compatibility


def generate_password(password_length=10):
    alphabet = "abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ!#@"
    password = ""

    for i in range(password_length):
        next_index = random.randrange(len(alphabet))
        password = password + alphabet[next_index]

    return password


def get_ip_address(request):
    if request is None:
        return None

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')  # Real IP address of client Machine
    return ip


def clear_cache():
    cache.clear()


def guess_extension(mime):
    """
    This function gets extensions from mimes, and if it can't find it uses the standard guesses
    :param mime: a mimetype string
    :return: a string containing a file extension eg. doc or docx
    """
    if mime == 'text/plain':
        extension = 'txt'
    elif mime == 'application/msword':
        extension = 'doc'
    elif mime == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        extension = 'docx'
    elif mime == 'application/vnd.oasis.opendocument.text':
        extension = 'odt'
    elif mime == 'text/html;charset=UTF-8':
        extension = 'html'
    else:
        extension = mimetypes.guess_extension(mime)

    return extension


def yes_or_no(question):
    while "the answer is invalid":
        reply = str(input(question + ' (y/n): ')).lower().strip()
        if reply[0] == 'y':
            return True
        if reply[0] == 'n':
            return False


def set_order(objects, order_attr_name, pk_list):
    """
    A generic implementation of model object ordering.
    :param: objects: a queryset or list of model objects
    :param: order_attr_name: string the model object's order attr name
    :param: pk_list: list of object PKs in order
    """
    ids = [int(id_) for id_ in pk_list]

    for object_ in objects:
        order = ids.index(object_.pk)
        setattr(object_, order_attr_name, order)
        object_.save()

    return objects

  
def day_month(date):
    return date.strftime("%d-%b")


def make_timezone_aware(date_string, date_string_format):
    return timezone.make_aware(
        datetime.strptime(date_string, date_string_format),
        timezone.get_current_timezone(),
    )


def create_language_override_redirect(
        request,
        url_name,
        kwargs,
        query_strings=None,
):
    if not query_strings:
        query_strings = {}

    query_strings['language'] = request.override_language
    if "email_template" in request.GET:
        query_strings['email_template'] = 'true'

    reverse_string = "{reverse}?{params}".format(
        reverse=reverse(url_name, kwargs=kwargs),
        params=urlencode(query_strings, quote_via=quote_plus)
    )

    return reverse_string


def language_override_redirect(request, url_name, kwargs, query_strings=None):
    reverse_string = create_language_override_redirect(
        request,
        url_name,
        kwargs,
        query_strings,
    )
    return redirect(reverse_string)
