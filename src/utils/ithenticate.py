__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
from xmlrpc import client as xmlrpclib
import os
import codecs

from utils import setting_handler


def ithenticate_is_enabled(journal):
    username = setting_handler.get_setting('crosscheck', 'username', journal).value
    password = setting_handler.get_setting('crosscheck', 'password', journal).value

    if username and password:
        return True
    else:
        return False


def build_server(journal):
    username = setting_handler.get_setting('crosscheck', 'username', journal).value
    password = setting_handler.get_setting('crosscheck', 'password', journal).value
    server = xmlrpclib.ServerProxy("https://api.ithenticate.com/rpc")
    login = server.login({"username": username, "password": password})

    assert(login['status'] == 200)
    sid = login['sid']

    return {'server': server, 'sid': sid}


def find_folder(server, sid, journal):
    found_folder = None
    folder_list_response = server.folder.list({'sid': sid})
    assert (folder_list_response['status'] == 200)

    for folder in folder_list_response['folders']:
        if folder['name'] == journal.name:
            found_folder = folder['id']
            break

    if found_folder is None:
        return None
    else:
        return found_folder


def make_folder(server, sid, journal):
    # Get the Ubiquity Press Folder then add a new journal folder inside and then return the id.
    folder_groups = server.group.list({'sid': sid})
    top_level_group = None

    if folder_groups['status'] == 200:
        for group in folder_groups['groups']:
            if group['name'] == 'My Folders':
                top_level_group = group['id']
                break

    new_folder = {'sid': sid, 'name': journal.name, 'folder_group': top_level_group, 'description': 'Journal Folder'}
    folder_add = server.folder.add(new_folder)
    return folder_add['id']


def send_to_ithenticate(article, file):
    # 1. Init Server
    server = build_server(article.journal)

    # 2. Try to get this journal's folder
    folder_id = find_folder(server['server'], server['sid'], article.journal)

    # 2.1 If the journal doesn't have a folder, make one
    if not folder_id:
        folder_id = make_folder(server['server'], server['sid'], article.journal)

    # 3. Prepare the submission

    first_author = article.correspondence_author

    open_file = codecs.open(file.self_article_path(), 'rb')
    data = xmlrpclib.Binary(bytes(open_file.read()))

    article_dict = {
        'title': article.title,
        'author_first': first_author.first_name,
        'author_last': first_author.last_name,
        'filename': os.path.basename(file.original_filename),
        'upload': data,
    }

    submission_dict = {
        'sid': server['sid'],
        'folder': folder_id,
        'uploads': [article_dict],
        'submit_to': 1,
    }

    submission = server['server'].document.add(
        submission_dict
    )

    if submission['status'] == 200:
        return submission['uploaded'][0].get('id')
    else:
        return None


def fetch_url(article):
    server = build_server(article.journal)

    try:
        document = server['server'].document.get({'id': int(article.ithenticate_id), 'sid': server['sid']})
        part_id = document['documents'][0]['parts'][0].get('id')
        report = server['server'].report.get({'id': int(part_id), 'sid': server['sid']})

        url = report['view_only_url']
    except KeyError:
        url = None

    return url


def fetch_percentage(journal, articles):
    server = build_server(journal)

    for article in articles:
        if article.ithenticate_id:
            document = server['server'].document.get({'id': int(article.ithenticate_id), 'sid': server['sid']})
            try:
                part = document['documents'][0]['parts'][0]
                if part['score']:
                    article.ithenticate_score = part['score']
                    article.save()
            except BaseException:
                pass
