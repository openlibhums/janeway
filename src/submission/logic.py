__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import warnings

from bs4 import BeautifulSoup

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.utils.translation import get_language, gettext_lazy as _

from core.forms import OrcidAffiliationForm
from core.model_utils import generate_dummy_email
from core import files
from core import models as core_models
from utils import orcid, setting_handler, shared as utils_shared
from utils.forms import clean_orcid_id
from submission import models
from submission.forms import AuthorForm, CreditRecordForm


def add_self_as_author(user, article):
    warnings.warn("'add_self_as_author' is deprecated and will be removed")
    return add_user_as_author(user, article)


def add_user_as_author(user, article, give_role=True):
    """ Assigns the given user as an author of the paper
    :param user: An instance of core.models.Account
    :param article: An instance of submission.models.Article
    :param give_role: If true, the user is given the author role in the journal
    """
    if give_role:
        submission_requires_authorisation = article.journal.get_setting(
            group_name='general',
            setting_name='limit_access_to_submission',
        )
        if submission_requires_authorisation and not user.check_role(article.journal, 'author'):
            role = core_models.Role.objects.get(
                slug='author',
            )
            core_models.AccessRequest.objects.get_or_create(
                journal=article.journal,
                user=user,
                role=role,
                text='Automatic request as author added to an article.',
            )
        else:
            user.add_account_role("author", article.journal)

    article.authors.add(user)
    models.ArticleAuthorOrder.objects.get_or_create(
        article=article,
        author=user,
        defaults={'order': article.next_author_sort()},
    )
    if not article.correspondence_author:
        article.correspondence_author = user
        article.save()
    return user


def check_author_exists(email):
    try:
        author = core_models.Account.objects.get(email=email)
        return author
    except core_models.Account.DoesNotExist:
        return False


def get_author(request, article):
    author_id = request.GET.get('author')
    frozen_authors = article.frozen_authors()
    try:
        author = frozen_authors.get(pk=author_id)
        return [author, 'author']
    except core_models.Account.DoesNotExist:
        return [None, None]


def get_agreement_text(journal):
    pub_fees = setting_handler.get_setting('general', 'publication_fees', journal).value
    sub_check = setting_handler.get_setting('general', 'submission_checklist', journal).value
    copy_notice = setting_handler.get_setting('general', 'copyright_notice', journal).value

    return "{0}\n\n{1}\n\n{2}".format(pub_fees, sub_check, copy_notice)


def check_file(uploaded_file, request, form):

    if not uploaded_file:
        form.add_error(None, 'You must select a file.')
        return False

    submission_formats = setting_handler.get_setting('general', 'limit_manuscript_types', request.journal).value

    if submission_formats:
        mime = files.guess_mime(str(uploaded_file.name))

        if mime in files.EDITABLE_FORMAT:
            return True
        else:
            form.add_error(None, _('You must upload a file that is either a Doc, Docx, RTF or ODT.'))
            return False
    else:
        return True


def get_text(soup, to_find):
    try:
        return soup.find(to_find).text
    except AttributeError:
        return ''


def parse_authors(soup):
    authors = soup.find_all('contrib')
    author_list = []
    for author in authors:
        first_name = get_text(author, 'given-names')
        last_name = get_text(author, 'surname')
        email = get_text(author, 'email')

        try:
            aff_id = author.find('xref').get('rid', None)
            aff = author.find('aff', attrs={'id': aff_id}).text
        except AttributeError:
            aff = get_text(author, 'aff')

        author_list.append({'first_name': first_name, 'last_name': last_name, 'email': email, 'institution': aff})

    return author_list


def add_keywords(soup, article):
    keywords = soup.find_all('kwd')

    for keyword in keywords:
        if keyword.text not in [None, '', ' ']:
            obj, c = models.Keyword.objects.get_or_create(
                word=str(keyword.text).strip(),
            )
            article.keywords.add(obj)


def import_from_jats_xml(path, journal, first_author_is_primary=False):
    with open(path) as file:
        soup = BeautifulSoup(file, 'lxml-xml')
        title = get_text(soup, 'article-title')
        abstract = get_text(soup, 'abstract')
        authors = parse_authors(soup)
        section = get_text(soup, 'subj-group')

        try:
            pub_date = soup.find('pub-date').get('iso-8601-date')
        except AttributeError:
            pub_date = None

        section_obj, created = models.Section.objects.get_or_create(name=section, journal=journal)

        article = models.Article.objects.create(
            title=title,
            abstract=abstract,
            section=section_obj,
            journal=journal,
            date_published=pub_date,
        )

        for author in authors:
            if not author.get('email') or author.get('email') == '':
                author['email'] = '{first}.{last}@journal.com'.format(first=author.get('first_name'),
                                                                      last=author.get('last_name'))
            try:
                author = core_models.Account.objects.get(Q(email=author['email']) | Q(username=author['email']))
            except core_models.Account.DoesNotExist:
                author = core_models.Account.objects.create(
                    email=author['email'],
                    username=author['email'],
                    first_name=author['first_name'],
                    last_name=author['last_name'],
                    institution=author['institution']
                )
            article.authors.add(author)
            models.ArticleAuthorOrder.objects.create(
                article=article,
                author=author,
                order=article.next_author_sort()
            )

        if first_author_is_primary and article.authors.all():
            article.correspondence_author = article.authors.all().first()
            article.save()

        add_keywords(soup, article)

        return article


def get_current_field(request, field_id):
    """
    Fetches a field based on whether there is a journal or press in the request object
    :param request: HttpRequest
    :param field_id: Field PK
    :return: Field Object
    """
    if field_id:
        if request.journal:
            field = get_object_or_404(models.Field, pk=field_id, journal=request.journal)
        else:
            field = get_object_or_404(models.Field, pk=field_id, press=request.press)
    else:
        field = None

    return field


def get_submission_fields(request):
    """
    Gets a queryset of fields base on whether there is a journal or press object present in request
    :param request: HttpRequest
    :return: A queryset of Field objects
    """

    if request.journal:
        fields = models.Field.objects.filter(journal=request.journal)
    else:
        fields = models.Field.objects.filter(press=request.press)

    return fields


def save_field(request, form):
    """
    Saves a form field and sets the press or journal parameter.
    :param request:
    :param form:
    :return:
    """

    new_field = form.save(commit=False)

    if request.journal:
        new_field.journal = request.journal
    else:
        new_field.press = request.press

    new_field.save()
    messages.add_message(request, messages.SUCCESS, 'Field saved.')
    return new_field


def delete_field(request):
    """
    Deletes a field object
    :param request: HttpRequest
    :return: None, adds a Message obejct to request
    """

    delete_id = request.POST.get('delete')
    field_to_delete = get_current_field(request, delete_id)
    field_to_delete.delete()
    messages.add_message(request, messages.SUCCESS, 'Field deleted. Existing answers will remain intact.')


def order_fields(request, fields):
    """
    Orders fields from a jquery sortable post.
    :param request: HttpRequest
    :param fields: Queryset of fields for this object
    :return: None
    """

    ids = [int(_id) for _id in request.POST.getlist('order[]')]

    for field in fields:
        order = ids.index(field.pk)
        field.order = order
        field.save()


def add_messages_for_author_order(request, author, change_order):
    sentences = {
        'first': _('%(author_name)s moved to the top.')
            % {'author_name': author.full_name()},
        'up':  _('%(author_name)s moved up.')
            % {'author_name': author.full_name()},
        'down':  _('%(author_name)s moved down.')
            % {'author_name': author.full_name()},
        'last':  _('%(author_name)s moved to the bottom.')
            % {'author_name': author.full_name()},
    }
    messages.add_message(
        request,
        messages.SUCCESS,
        sentences[change_order],
    )


def save_author_order(author, change_order, article):
    all_authors = [
        order.author for order in article.articleauthororder_set.all()
    ]
    old_order = all_authors.index(author)
    new_orders = {
        'first': 0,
        'up': max(old_order - 1, 0),
        'down': min(old_order + 1, len(all_authors) - 1),
        'last': len(all_authors) - 1,
    }
    new_order = new_orders[change_order]
    if old_order == new_order:
        return False
    all_authors.pop(old_order)
    all_authors.insert(new_order, author)
    for i, each_author in enumerate(all_authors):
        models.ArticleAuthorOrder.objects.update_or_create(
            article=article,
            author=each_author,
            defaults={'order': i},
        )
    return True


def save_frozen_author_order(frozen_author, change_order, article):
    all_frozen_authors = [fa for fa in article.frozen_authors()]
    old_order = all_frozen_authors.index(frozen_author)
    new_orders = {
        'first': 0,
        'up': max(old_order - 1, 0),
        'down': min(old_order + 1, len(all_frozen_authors) - 1),
        'last': len(all_frozen_authors) - 1,
    }
    new_order = new_orders[change_order]
    if old_order == new_order:
        return False
    all_frozen_authors.pop(old_order)
    all_frozen_authors.insert(new_order, frozen_author)
    for i, each_frozen_author in enumerate(all_frozen_authors):
        each_frozen_author.order = i
        each_frozen_author.save()
    return True


def add_author_from_search(request, article):
    search_term = request.POST.get('author_search_text')
    query = Q(email=search_term)
    try:
        cleaned_orcid = clean_orcid_id(search_term)
        query |= Q(orcid__contains=cleaned_orcid)
    except ValueError:
        cleaned_orcid = ''

    try:
        new_author = core_models.Account.objects.get(query)
    except core_models.Account.DoesNotExist:
        new_author = None
    added = False

    if cleaned_orcid:
        orcid_details = orcid.get_orcid_record_details(cleaned_orcid)
        emails = orcid_details.get("emails", [])
    else:
        orcid_details = {}
        emails = []

    # First check if there is a Janeway account with an email address
    # that matches an email address in a public ORCiD record.
    if not new_author and emails:
        for email in emails:
            candidates = core_models.Account.objects.filter(email=email)
            if candidates.exists():
                candidates.update(orcid=cleaned_orcid)
                new_author = candidates.first()
                break

    # Otherwise, check if there is at least one public email address in the
    # ORCiD record, or make a fake email, and then make an account.
    if not new_author and orcid_details:
        if emails:
            email = emails[0]
        else:
            email = generate_dummy_email(orcid_details)

        form = AuthorForm(
            {
                'email': email,
                'first_name': orcid_details.get('first_name', ''),
                'last_name': orcid_details.get('last_name', ''),
            }
        )
        if form.is_valid():
            new_author = form.save(commit=False)
            new_author.set_password(utils_shared.generate_password())
            new_author.orcid = cleaned_orcid
            new_author.save()

    # If we now have an account, link the article.
    if new_author:
        if new_author not in article.authors.all():
            add_user_as_author(new_author, article)
            added = True
            messages.add_message(
                request,
                messages.SUCCESS,
                _('%(author_name)s (%(email)s) added to the article.')
                    % {
                        "author_name": new_author.full_name(),
                        "email": new_author.email
                    },
            )
        else:
            messages.add_message(
                request,
                messages.INFO,
                _('%(author_name)s (%(email)s) is already an author.')
                    % {
                        "author_name": new_author.full_name(),
                        "email": new_author.email,
                    },
            )
    else:
        messages.add_message(
            request, messages.WARNING,
            _('No author found with search term: "%(search_term)s".')
            % {"search_term" : search_term},
        )

    # If the author has no affiliations, create them from the ORCiD record.
    if new_author and not new_author.affiliations.exists() and orcid_details:
        for orcid_affil in orcid_details.get("affiliations", []):
            orcid_affil_form = OrcidAffiliationForm(
                orcid_affiliation=orcid_affil,
                tzinfo=new_author.preferred_timezone,
                data={'account': new_author}
            )
            if orcid_affil_form.is_valid():
                affiliation = orcid_affil_form.save()
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _("Affiliation created: %(affiliation)s")
                        % {"affiliation": affiliation},
                )

    return new_author, added


def add_author_from_manual_entry(request, article):
    form = AuthorForm(request.POST)

    email = request.POST.get("email")
    author = None
    added = False
    account_exists = check_author_exists(email=email)
    if account_exists:
        author = core_models.Account.objects.get(email=email)
    elif form.is_valid():
        new_author = form.save(commit=False)
        new_author.set_password(utils_shared.generate_password())
        new_author.save()
        author = new_author
    else:
        messages.add_message(
            request, messages.WARNING,
            _('Could not add the author manually.'),
        )

    if author:
        if author in article.authors.all():
            messages.add_message(
                request, messages.SUCCESS,
                _('%(author_name)s (%(email)s) is already an author.')
                    % {
                        "author_name": author.full_name(),
                        "email": author.email
                    },
            )
        else:
            add_user_as_author(author, article)
            added = True
            messages.add_message(
                request, messages.SUCCESS,
                _('%(author_name)s (%(email)s) added to the article.')
                    % {
                        "author_name": author.full_name(),
                        "email": author.email
                    },
            )
    return author, added


def set_correspondence_author(request, article):
    author = get_object_or_404(
        core_models.Account,
        pk=request.POST.get('corr_author', None),
        authors=article,
        authors__journal=request.journal,
    )
    article.correspondence_author = author
    article.save()
    messages.add_message(
        request,
        messages.SUCCESS,
        _('%(author_name)s (%(email)s) made correspondence author.')
            % {
                "author_name": author.full_name(),
                "email": author.email
            },
    )
    return author


def add_credit_role(request, article, author=None, frozen_author=None):
    form = CreditRecordForm(request.POST)
    if form.is_valid() and (author or frozen_author):
        record = form.save()
        record.article = article
        record.author = author
        record.frozen_author = frozen_author
        record.save()
        name = author.full_name() if author else frozen_author.full_name()
        messages.add_message(
            request,
            messages.SUCCESS,
            _('%(author_name)s was given role %(role)s.')
                % {
                    "author_name": name,
                    "role": record.get_role_display(),
                },
        )
