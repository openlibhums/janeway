__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import warnings

from bs4 import BeautifulSoup

from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils.translation import get_language, gettext_lazy as _

from core.forms import OrcidAffiliationForm
from core.model_utils import generate_dummy_email
from core import files
from core import models as core_models
from utils import orcid, setting_handler, shared as utils_shared
from utils.forms import clean_orcid_id
from submission import models
from submission.forms import EditFrozenAuthor, CreditRecordForm


def add_self_as_author(user, article):
    warnings.warn("'add_self_as_author' is deprecated and will be removed")
    return add_user_as_author(user, article)


def add_user_as_author(user, article, give_role=True):
    """Assigns the given user as an author of the paper
    :param user: An instance of core.models.Account
    :param article: An instance of submission.models.Article
    :param give_role: If true, the user is given the author role in the journal
    """
    raise DeprecationWarning("Use FrozenAuthor instead.")
    if give_role:
        submission_requires_authorisation = article.journal.get_setting(
            group_name="general",
            setting_name="limit_access_to_submission",
        )
        if submission_requires_authorisation and not user.check_role(
            article.journal, "author"
        ):
            role = core_models.Role.objects.get(
                slug="author",
            )
            core_models.AccessRequest.objects.get_or_create(
                journal=article.journal,
                user=user,
                role=role,
                text="Automatic request as author added to an article.",
            )
        else:
            user.add_account_role("author", article.journal)

    article.authors.add(user)
    models.ArticleAuthorOrder.objects.get_or_create(
        article=article,
        author=user,
        defaults={"order": article.next_author_sort()},
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
    author_id = request.GET.get("author")
    frozen_authors = article.frozen_authors()
    try:
        author = frozen_authors.get(pk=author_id)
        return [author, "author"]
    except models.FrozenAuthor.DoesNotExist:
        return [None, None]


def get_agreement_text(journal):
    pub_fees = setting_handler.get_setting("general", "publication_fees", journal).value
    sub_check = setting_handler.get_setting(
        "general", "submission_checklist", journal
    ).value
    copy_notice = setting_handler.get_setting(
        "general", "copyright_notice", journal
    ).value

    return "{0}\n\n{1}\n\n{2}".format(pub_fees, sub_check, copy_notice)


def check_file(uploaded_file, request, form):
    if not uploaded_file:
        form.add_error(None, "You must select a file.")
        return False

    submission_formats = setting_handler.get_setting(
        "general", "limit_manuscript_types", request.journal
    ).value

    if submission_formats:
        mime = files.guess_mime(str(uploaded_file.name))

        if mime in files.EDITABLE_FORMAT:
            return True
        else:
            form.add_error(
                None,
                _("You must upload a file that is either a Doc, Docx, RTF or ODT."),
            )
            return False
    else:
        return True


def get_text(soup, to_find):
    try:
        return soup.find(to_find).text
    except AttributeError:
        return ""


def parse_authors(soup):
    authors = soup.find_all("contrib")
    author_list = []
    for author in authors:
        first_name = get_text(author, "given-names")
        last_name = get_text(author, "surname")
        email = get_text(author, "email")

        try:
            aff_id = author.find("xref").get("rid", None)
            aff = author.find("aff", attrs={"id": aff_id}).text
        except AttributeError:
            aff = get_text(author, "aff")

        author_list.append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "institution": aff,
            }
        )

    return author_list


def add_keywords(soup, article):
    keywords = soup.find_all("kwd")

    for keyword in keywords:
        if keyword.text not in [None, "", " "]:
            obj, c = models.Keyword.objects.get_or_create(
                word=str(keyword.text).strip(),
            )
            article.keywords.add(obj)


def import_from_jats_xml(path, journal, first_author_is_primary=False):
    raise DeprecationWarning("Use the JATS importer in the imports plugin instead.")
    with open(path) as file:
        soup = BeautifulSoup(file, "lxml-xml")
        title = get_text(soup, "article-title")
        abstract = get_text(soup, "abstract")
        authors = parse_authors(soup)
        section = get_text(soup, "subj-group")

        try:
            pub_date = soup.find("pub-date").get("iso-8601-date")
        except AttributeError:
            pub_date = None

        section_obj, created = models.Section.objects.get_or_create(
            name=section, journal=journal
        )

        article = models.Article.objects.create(
            title=title,
            abstract=abstract,
            section=section_obj,
            journal=journal,
            date_published=pub_date,
        )

        for author in authors:
            if not author.get("email") or author.get("email") == "":
                author["email"] = "{first}.{last}@journal.com".format(
                    first=author.get("first_name"), last=author.get("last_name")
                )
            try:
                author = core_models.Account.objects.get(
                    Q(email=author["email"]) | Q(username=author["email"])
                )
            except core_models.Account.DoesNotExist:
                author = core_models.Account.objects.create(
                    email=author["email"],
                    username=author["email"],
                    first_name=author["first_name"],
                    last_name=author["last_name"],
                    institution=author["institution"],
                )
            article.authors.add(author)
            models.ArticleAuthorOrder.objects.create(
                article=article, author=author, order=article.next_author_sort()
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
            field = get_object_or_404(
                models.Field, pk=field_id, journal=request.journal
            )
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
    messages.add_message(request, messages.SUCCESS, "Field saved.")
    return new_field


def delete_field(request):
    """
    Deletes a field object
    :param request: HttpRequest
    :return: None, adds a Message obejct to request
    """

    delete_id = request.POST.get("delete")
    field_to_delete = get_current_field(request, delete_id)
    field_to_delete.delete()
    messages.add_message(
        request, messages.SUCCESS, "Field deleted. Existing answers will remain intact."
    )


def order_fields(request, fields):
    """
    Orders fields from a jquery sortable post.
    :param request: HttpRequest
    :param fields: Queryset of fields for this object
    :return: None
    """

    ids = [int(_id) for _id in request.POST.getlist("order[]")]

    for field in fields:
        order = ids.index(field.pk)
        field.order = order
        field.save()


def save_author_order(request, article):
    raise DeprecationWarning("Use save_frozen_author_order instead.")
    author_pks = [int(pk) for pk in request.POST.getlist("authors[]")]
    for author in article.authors.all():
        order = author_pks.index(author.pk)
        author_order, c = models.ArticleAuthorOrder.objects.get_or_create(
            article=article, author=author, defaults={"order": order}
        )

        if not c:
            author_order.order = order
            author_order.save()


def save_frozen_author_order(request, article):
    """
    Calculate and make the needed change to FrozenAuthor.order
    for each of the authors on the article.
    request: HttpRequest with POST data including author_pk
             and change_order (enum: "top", "up", "down", "bottom")
    """
    changed = False
    author_id = request.POST.get("author_pk")
    try:
        author_id = int(author_id)
    except TypeError:
        raise ValidationError("Invalid author ID submitted")
    author = get_object_or_404(
        models.FrozenAuthor,
        pk=author_id,
        article=article,
    )
    change_order = request.POST.get("change_order")
    all_authors = list(article.frozenauthor_set.all())
    old_order = all_authors.index(author)
    new_orders = {
        "top": 0,
        "up": max(old_order - 1, 0),
        "down": min(old_order + 1, len(all_authors) - 1),
        "bottom": len(all_authors) - 1,
    }
    new_order = new_orders[change_order]
    if old_order != new_order:
        all_authors.pop(old_order)
        all_authors.insert(new_order, author)
        for i, each_author in enumerate(all_authors):
            each_author.order = i
            each_author.save()
        changed = True

    if changed:
        messages.add_message(
            request,
            messages.SUCCESS,
            _("%(author_name)s is now in position %(position)s.")
            % {
                "author_name": author.full_name(),
                "position": str(author.order + 1),
            },
        )
    else:
        messages.add_message(
            request,
            messages.INFO,
            _("%(author_name)s is already in position %(position)s.")
            % {
                "author_name": author.full_name(),
                "position": str(author.order + 1),
            },
        )
    return author


def add_author_using_email(search_term, article):
    email = search_term
    author, created = models.FrozenAuthor.get_or_snapshot_if_email_found(
        email,
        article,
    )
    return author, created


def add_author_using_orcid(search_term, article, request):
    author = None
    created = False
    # Prep ORCID details if available
    try:
        cleaned_orcid = clean_orcid_id(search_term)
    except ValueError:
        cleaned_orcid = ""
        return author, created

    author, created = models.FrozenAuthor.get_or_snapshot_if_orcid_found(
        cleaned_orcid,
        article,
    )
    if author:
        return author, created

    # If there is no account or frozen author in Janeway with that orcid and article,
    # get the public ORCID record.
    orcid_details = orcid.get_orcid_record_details(cleaned_orcid)
    orcid_emails = orcid_details.get("emails", [])

    # Check for accounts by email address.
    for email in orcid_emails:
        try:
            account = core_models.Account.objects.get(
                email=email,
                orcid__isnull=True,
            )
            account.orcid = cleaned_orcid
            account.save()
            author = account.snapshot_as_author(article)
            created = True
            return author, created
        except core_models.Account.DoesNotExist:
            author = None

    # Otherwise, make one.
    form = EditFrozenAuthor(
        {
            "frozen_email": orcid_emails[0] if orcid_emails else "",
            "first_name": orcid_details.get("first_name", ""),
            "last_name": orcid_details.get("last_name", ""),
        }
    )
    if form.is_valid():
        author = form.save(commit=False)
        author.article = article
        author.frozen_orcid = cleaned_orcid
        author.order = article.next_frozen_author_order()
        author.save()
        created = True

    if created:
        add_author_affiliation_from_orcid(author, orcid_details, request)

    return author, created


def add_author_affiliation_from_orcid(author, orcid_details, request):
    orcid_affils = orcid_details.get("affiliations", [])
    if orcid_affils:
        tzinfo = author.author.preferred_timezone if author.author else None
        orcid_affil_form = OrcidAffiliationForm(
            orcid_affiliation=orcid_affils[0],
            tzinfo=tzinfo,
            data={"frozen_author": author},
        )
        if orcid_affil_form.is_valid():
            affiliation = orcid_affil_form.save()


def add_author_from_search(search_term, request, article):
    """
    Tries to add a FrozenAuthor from a search query.
    """
    author, created = add_author_using_email(search_term, article)
    if not author:
        author, created = add_author_using_orcid(search_term, article, request)

    if author:
        if created:
            messages.add_message(
                request,
                messages.SUCCESS,
                _("%(author_name)s is now an author.")
                % {
                    "author_name": author.full_name(),
                },
            )
        else:
            messages.add_message(
                request,
                messages.INFO,
                _("%(author_name)s is already an author.")
                % {
                    "author_name": author.full_name(),
                },
            )
    else:
        messages.add_message(
            request,
            messages.WARNING,
            _('No author found with search term: "%(search_term)s".')
            % {"search_term": search_term},
        )

    return author


def add_new_author_from_form(request, article):
    new_author_form = EditFrozenAuthor(request.POST)
    author = None

    frozen_email = request.POST.get("frozen_email")
    if frozen_email:
        authors = models.FrozenAuthor.objects.filter(
            Q(article=article)
            & (Q(frozen_email=frozen_email) | Q(author__username__iexact=frozen_email))
        )
        if authors.exists():
            author = authors.first()

    if not author and new_author_form.is_valid():
        author = new_author_form.save()
        author.article = article
        author.order = article.next_frozen_author_order()
        author.save()
    else:
        messages.add_message(
            request,
            messages.WARNING,
            _("Could not add the author manually."),
        )

    if author:
        messages.add_message(
            request,
            messages.SUCCESS,
            _("%(author_name)s (%(email)s) added to the article.")
            % {"author_name": author.full_name(), "email": author.email},
        )
    return author


def save_correspondence_author(request, article):
    account = get_object_or_404(
        core_models.Account,
        pk=request.POST.get("corr_author", None),
        frozenauthor__article=article,
    )
    article.correspondence_author = account
    article.save()
    messages.add_message(
        request,
        messages.SUCCESS,
        _("%(author_name)s (%(email)s) made correspondence author.")
        % {"author_name": account.full_name(), "email": account.email},
    )
    author = account.frozen_author(article)
    return author


def get_credit_form(request, author):
    use_credit = setting_handler.get_setting(
        "general",
        "use_credit",
        journal=request.journal,
    ).processed_value
    if use_credit:
        return CreditRecordForm(
            frozen_author=author,
        )
    else:
        return None


def add_credit_role(request, article):
    author_id = request.POST.get("author_pk")
    try:
        author_id = int(author_id)
    except TypeError:
        raise ValidationError("Invalid author ID submitted")
    author = get_object_or_404(
        models.FrozenAuthor,
        pk=author_id,
        article=article,
    )
    credit_form = CreditRecordForm(
        request.POST,
        frozen_author=author,
    )
    if credit_form.is_valid() and author:
        record = credit_form.save()
        record.frozen_author = author
        record.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            _("%(author_name)s now has role %(role)s.")
            % {
                "author_name": author.full_name(),
                "role": record.get_role_display(),
            },
        )
    return author


def remove_credit_role(request, article):
    credit_id = request.POST.get("credit_pk")
    try:
        credit_id = int(credit_id)
    except TypeError:
        raise ValidationError("Invalid credit ID submitted")
    record = get_object_or_404(
        models.CreditRecord,
        pk=credit_id,
        frozen_author__article=article,
    )
    author = record.frozen_author
    role_display = record.get_role_display()
    record.delete()
    messages.add_message(
        request,
        messages.SUCCESS,
        _("%(author_name)s no longer has the role %(role)s.")
        % {
            "author_name": author.full_name(),
            "role": role_display,
        },
    )
    return author
