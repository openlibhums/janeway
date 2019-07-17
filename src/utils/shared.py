__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import random
import mimetypes

from django.core.cache import cache

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
