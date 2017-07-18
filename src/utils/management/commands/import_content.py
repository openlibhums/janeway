import sys
import requests
from bs4 import BeautifulSoup

from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType

from press import models as press_models
from journal import models as journal_models
from cms import models as cms_models


def get_nav_children(children):
    child_list = list()
    for litag in children.find_all('li'):
        a = litag.find('a', href=True)
        child_list.append(
            {'text': a.text,
             'href': a.attrs['href']}
        )
    return child_list


def get_nav(text, nav, child_identifier):
    nav_list = list()
    soup = BeautifulSoup(text, 'html.parser')
    ultag = soup.find('ul', {'class': nav})

    for litag in ultag.find_all('li', {'class': child_identifier}):
        children = litag.find('ul')

        a = litag.find('a', href=True)
        nav_list.append(
            {'text': a.text,
             'href': a.attrs['href'],
             'children': get_nav_children(children)}
        )

    return nav_list


def generate_cms_pages(object, nav_items, content):

    for item in nav_items:
        print('Fetching ', item['href'])
        r = requests.get(item['href'])
        soup = BeautifulSoup(r.text, 'html.parser')
        html = soup.find('div', {'class': content})

        if html is not None:
            content_type = ContentType.objects.get_for_model(object)
            new_cms_page = cms_models.Page.objects.create(
                content_type=content_type,
                object_id=object.pk,
                name=slugify(item.get('text')),
                display_name=item.get('text'),
                content=html.prettify(),
                is_markdown=False,
            )

            nav_item = generate_nav_entry(object,
                                          new_cms_page,
                                          True if item['children'] else False,
                                          False)

        for child in item['children']:
            print('Fetching ', child['href'])
            r = requests.get(child['href'])
            soup = BeautifulSoup(r.text, 'html.parser')
            html = soup.find('div', {'class': content})
            name = "{0}/{1}".format(new_cms_page.name, slugify(child.get('text')))

            if html is not None:
                content_type = ContentType.objects.get_for_model(object)
                child_cms_page = cms_models.Page.objects.create(
                    content_type=content_type,
                    object_id=object.pk,
                    name=name,
                    display_name=child.get('text'),
                    content=html.prettify(),
                    is_markdown=False,
                )

                generate_nav_entry(object,
                                   child_cms_page,
                                   False,
                                   new_cms_page,
                                   nav_item)


def generate_nav_entry(object, cms_page, has_children=False, parent=None, parent_nav_item=None):

    new_nav_item = cms_models.NavigationItem.objects.create(
        object=object,
        link_name=cms_page.display_name,
        link="site/{0}".format(cms_page.name),
        has_sub_nav=True if has_children else False,
        top_level_nav=parent_nav_item,
    )

    return new_nav_item


class Command(BaseCommand):
    """
    Takes a UL arg and a CONTENT arg to import content
    """

    help = "Deletes duplicate settings."

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument('--journal_id', default=False)
        parser.add_argument('--url')
        parser.add_argument('--ul')
        parser.add_argument('--child_identifier')
        parser.add_argument('--content')

    def handle(self, *args, **options):
        """Takes a UL and CONTENT arg to import content into the CMS.

        :param args: None
        :param options: None
        :return: None
        """
        journal_id = options.get('journal_id')
        url = options.get('url')
        ul = options.get('ul')
        child_identifier = options.get('child_identifier')
        content = options.get('content')

        if journal_id == 'press':
            object = press_models.Press.objects.all()[0]
        else:
            object = journal_models.Journal.objects.filter(pk=journal_id)

        if not object:
            print('No object (journal or press) was found.')
            sys.exit()

        print("Object to generate nav for {0}".format(object))
        print("Fetching nav items")

        r = requests.get(url).text
        nav_items = get_nav(r, ul, child_identifier)

        print("Found {0} primary nav items".format(len(nav_items)))
        print("Generating CMS pages.")

        generate_cms_pages(object, nav_items, content)
