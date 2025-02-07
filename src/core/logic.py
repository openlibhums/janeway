__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os
from PIL import Image, UnidentifiedImageError
import uuid
from importlib import import_module
from datetime import timedelta
import operator
import re
from functools import reduce

from django.conf import settings
from django.contrib.auth import logout
from django.contrib import messages
from django.template.loader import get_template
from django.db.models import Q
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _

from core import models, files, plugin_installed_apps
from utils.function_cache import cache
from review import models as review_models
from utils import render_template, notify_helpers, setting_handler
from submission import models as submission_models
from comms import models as comms_models
from utils import shared
from utils.logger import get_logger

logger = get_logger(__name__)


def send_reset_token(request, reset_token):
    core_reset_password_url = request.site_type.site_url(
        reverse(
            'core_reset_password',
            kwargs={'token': reset_token.token},
        )
    )
    context = {
        'reset_token': reset_token,
        'core_reset_password_url': core_reset_password_url,
    }
    log_dict = {'level': 'Info', 'types': 'Reset Token', 'target': None}
    if not request.journal:
        message = render_template.get_message_content(
            request,
            context,
            request.press.password_reset_text,
            template_is_setting=True,
        )
    else:
        message = render_template.get_message_content(
            request,
            context,
            'password_reset',
        )

    subject = 'subject_password_reset'

    notify_helpers.send_email_with_body_from_user(
        request,
        subject,
        reset_token.account.email,
        message,
        log_dict=log_dict,
    )


def send_confirmation_link(request, new_user):
    core_confirm_account_url = request.site_type.site_url(
        reverse(
            'core_confirm_account',
            kwargs={'token': new_user.confirmation_code},
        )
    )
    context = {
        'user': new_user,
        'core_confirm_account_url': core_confirm_account_url,
    }
    if not request.journal:
        message = render_template.get_message_content(
            request,
            context,
            request.press.registration_text,
            template_is_setting=True,
        )
    else:
        message = render_template.get_message_content(
            request,
            context,
            'new_user_registration',
        )

    subject = 'subject_new_user_registration'

    notify_helpers.send_slack(
        request,
        'New registration: {0}'.format(new_user.full_name()),
        ['slack_admins'],
    )
    log_dict = {'level': 'Info', 'types': 'Account Confirmation', 'target': None}
    notify_helpers.send_email_with_body_from_user(
        request,
        subject,
        new_user.email,
        message,
        log_dict=log_dict,
    )


def resize_and_crop(img_path, size, crop_type='middle'):
    """
    Resize and crop an image to fit the specified size.
    """

    # If height is higher we resize vertically, if not we resize horizontally
    try:
        img = Image.open(img_path)
    except FileNotFoundError:
        logger.warning("File not found, can't resize: %s" % img_path)
        return
    except UnidentifiedImageError:
        # Could be an SVG
        return

    # Get current and desired ratio for the images
    img_ratio = img.size[0] / float(img.size[1])
    ratio = size[0] / float(size[1])
    # The image is scaled/cropped vertically or horizontally depending on the ratio
    if ratio > img_ratio:
        img = img.resize(
            (size[0], int(size[0] * img.size[1] // img.size[0])),
            Image.LANCZOS,
        )
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, img.size[0], size[1])
        elif crop_type == 'middle':
            box = (0, (img.size[1] - size[1]) // 2, img.size[0], (img.size[1] + size[1]) // 2)
        elif crop_type == 'bottom':
            box = (0, img.size[1] - size[1], img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')
        img = img.crop(box)

    elif ratio < img_ratio:
        img = img.resize(
            (size[0], int(size[0] * img.size[1] // img.size[0])),
            Image.LANCZOS,
        )
        # Crop in the top, middle or bottom
        if crop_type == 'top':
            box = (0, 0, size[0], img.size[1])
        elif crop_type == 'middle':
            horizontal_padding = (size[0] - img.size[0]) // 2
            vertical_padding = (size[1] - img.size[1]) // 2

            offset_tuple = (horizontal_padding, vertical_padding)

            final_thumb = Image.new(mode='RGBA', size=size, color=(255, 255, 255, 0))
            final_thumb.paste(img, offset_tuple)  # paste the thumbnail into the full sized image

            final_thumb.save(img_path, "png")
            return
        elif crop_type == 'bottom':
            box = (img.size[0] - size[0], 0, img.size[0], img.size[1])
        else:
            raise ValueError('ERROR: invalid value for crop_type')

        img = img.crop(box)
    else:
        img = img.resize((size[0], size[1]), Image.LANCZOS)

    if img.mode == "CMYK":
        img = img.convert("RGB")

    img.save(img_path, "png")


def settings_for_context(request):
    if request.journal:
        return cached_settings_for_context(request.journal, get_language())
    else:
        return {}


@cache(600)
def cached_settings_for_context(journal, language):
    setting_groups = ['general', 'crosscheck', 'article', 'news', 'styling']
    _dict = {group: {} for group in setting_groups}

    for group in setting_groups:
        settings = models.Setting.objects.filter(group__name=group)

        for setting in settings:
            _dict[group][setting.name] = setting_handler.get_setting(
                group,
                setting.name,
                journal,
            ).processed_value
    return _dict


def process_setting_list(settings_to_get, type, journal):
    settings = []
    for setting in settings_to_get:
        settings.append({
            'name': setting,
            'object': setting_handler.get_setting(type, setting, journal),
        })

    return settings


def get_settings_to_edit(display_group, journal, user):
    review_form_choices = list()
    for form in review_models.ReviewForm.objects.filter(
        journal=journal,
        deleted=False,
    ):
        review_form_choices.append([form.pk, form])

    if display_group == 'submission':
        group_of_settings = [
            {'name': 'disable_journal_submission',
             'object': setting_handler.get_setting('general', 'disable_journal_submission', journal)
             },
            {'name': 'disable_journal_submission_message',
             'object': setting_handler.get_setting('general', 'disable_journal_submission_message', journal)
             },
            {'name': 'limit_access_to_submission',
             'object': setting_handler.get_setting('general', 'limit_access_to_submission', journal)
             },
            {'name': 'submission_access_request_text',
             'object': setting_handler.get_setting('general', 'submission_access_request_text', journal)
             },
            {'name': 'submission_access_request_contact',
             'object': setting_handler.get_setting('general', 'submission_access_request_contact', journal)
             },
            {'name': 'abstract_required',
             'object': setting_handler.get_setting(
                 'general',
                 'abstract_required',
                 journal,
             )
             },
            {'name': 'submission_intro_text',
             'object': setting_handler.get_setting(
                 'general',
                 'submission_intro_text',
                 journal
             )
             },
            {'name': 'copyright_notice',
             'object': setting_handler.get_setting('general', 'copyright_notice', journal)
             },
            {'name': 'submission_checklist',
             'object': setting_handler.get_setting('general', 'submission_checklist', journal)
             },
            {'name': 'acceptance_criteria',
             'object': setting_handler.get_setting('general', 'acceptance_criteria', journal)
             },
            {'name': 'publication_fees',
             'object': setting_handler.get_setting('general', 'publication_fees', journal)
             },
            {'name': 'editors_for_notification',
             'object': setting_handler.get_setting('general', 'editors_for_notification', journal),
             'choices': journal.editor_pks()
             },
            {'name': 'user_automatically_author',
             'object': setting_handler.get_setting('general', 'user_automatically_author', journal),
             },
            {'name': 'submission_summary',
             'object': setting_handler.get_setting('general', 'submission_summary', journal),
             },
            {'name': 'limit_manuscript_types',
             'object': setting_handler.get_setting('general', 'limit_manuscript_types', journal),
             },
            {'name': 'accepts_preprint_submissions',
             'object': setting_handler.get_setting('general', 'accepts_preprint_submissions', journal),
             },
            {'name': 'focus_and_scope',
             'object': setting_handler.get_setting('general', 'focus_and_scope', journal),
             },
            {'name': 'publication_cycle',
             'object': setting_handler.get_setting('general', 'publication_cycle', journal),
             },
            {'name': 'peer_review_info',
             'object': setting_handler.get_setting('general', 'peer_review_info', journal),
             },
            {'name': 'copyright_submission_label',
             'object': setting_handler.get_setting('general', 'copyright_submission_label', journal)
             },
            {
                'name': 'file_submission_guidelines',
                'object': setting_handler.get_setting(
                    'general',
                    'file_submission_guidelines', journal
                ),
            },
            {
                'name': 'manuscript_file_submission_instructions',
                'object': setting_handler.get_setting(
                    'general',
                    'manuscript_file_submission_instructions', journal
                ),
            },
            {
                'name': 'data_figure_file_submission_instructions',
                'object': setting_handler.get_setting(
                    'general',
                    'data_figure_file_submission_instructions', journal
                ),
            },
            {
                'name': 'hide_editors_from_authors',
                'object': setting_handler.get_setting(
                    'general',
                    'hide_editors_from_authors', journal
                ),
            }
        ]
        setting_group = 'general'

    elif display_group == 'review':
        group_of_settings = [
            {
                'name': 'reviewer_guidelines',
                'object': setting_handler.get_setting('general', 'reviewer_guidelines', journal),
            },
            {
                'name': 'default_review_visibility',
                'object': setting_handler.get_setting('general', 'default_review_visibility', journal),
                'choices': review_models.review_visibilty()
            },
            {
                'name': 'review_file_help',
                'object': setting_handler.get_setting('general', 'review_file_help', journal),
            },
            {
                'name': 'default_review_days',
                'object': setting_handler.get_setting('general', 'default_review_days', journal),
            },
            {
                'name': 'enable_save_review_progress',
                'object': setting_handler.get_setting('general', 'enable_save_review_progress', journal),
            },
            {
                'name': 'enable_one_click_access',
                'object': setting_handler.get_setting('general', 'enable_one_click_access', journal),
            },
            {
                'name': 'enable_expanded_review_details',
                'object': setting_handler.get_setting('general', 'enable_expanded_review_details', journal),
            },
            {
                'name': 'draft_decisions',
                'object': setting_handler.get_setting('general', 'draft_decisions', journal),
            },
            {
                'name': 'enable_study_topics',
                'object': setting_handler.get_setting('general', 'enable_study_topics', journal),
            },
            {
                'name': 'default_review_form',
                'object': setting_handler.get_setting('general', 'default_review_form', journal),
                'choices': review_form_choices
            },
            {
                'name': 'reviewer_form_download',
                'object': setting_handler.get_setting('general', 'reviewer_form_download', journal),
            },
            {
                'name': 'peer_review_upload_text',
                'object': setting_handler.get_setting('general', 'peer_review_upload_text', journal),
            },
            {
                'name': 'enable_peer_review_data_block',
                'object': setting_handler.get_setting('general', 'enable_peer_review_data_block', journal),
            },
            {
                'name': 'hide_review_data_pre_release',
                'object': setting_handler.get_setting('general', 'hide_review_data_pre_release', journal),
            },
            {
                'name': 'enable_suggested_reviewers',
                'object': setting_handler.get_setting('general', 'enable_suggested_reviewers', journal),
            },
            {
                'name': 'enable_peer_review_data_on_review_page',
                'object': setting_handler.get_setting('general', 'enable_peer_review_data_on_review_page', journal),
            },
            {
                'name': 'accept_article_warning',
                'object': setting_handler.get_setting('general', 'accept_article_warning', journal),
            },
            {
                'name': 'open_peer_review',
                'object': setting_handler.get_setting('general', 'open_peer_review', journal),
            },
            {
                'name': 'open_review_default_opt_in',
                'object': setting_handler.get_setting('general', 'open_review_default_opt_in', journal),
            },
            {
                'name': 'disable_reviewer_recommendation',
                'object': setting_handler.get_setting('general', 'disable_reviewer_recommendation', journal),
            },
            {
                'name': 'enable_share_reviews_decision',
                'object': setting_handler.get_setting('general', 'enable_share_reviews_decision', journal),
            },
            {
                'name': 'display_completed_reviews_in_additional_rounds',
                'object': setting_handler.get_setting('general', 'display_completed_reviews_in_additional_rounds', journal),
            },
            {
                'name': 'share_author_response_letters',
                'object': setting_handler.get_setting('general', 'share_author_response_letters', journal),
            },
            {
                'name': 'display_completed_reviews_in_additional_rounds_text',
                'object': setting_handler.get_setting('general', 'display_completed_reviews_in_additional_rounds_text', journal),
            },
            {
                'name': 'enable_custom_editor_assignment',
                'object': setting_handler.get_setting('general', 'enable_custom_editor_assignment', journal),
            },
        ]
        setting_group = 'general'

    elif display_group == 'crossref':
        xref_settings = [
            'use_crossref', 'crossref_test', 'crossref_username', 'crossref_password', 'crossref_email',
            'crossref_name', 'crossref_prefix', 'crossref_registrant', 'doi_display_prefix', 'doi_display_suffix',
            'doi_pattern', 'doi_manager_action_maximum_size', 'title_doi', 'issue_doi_pattern', 'register_issue_dois'
        ]

        group_of_settings = process_setting_list(xref_settings, 'Identifiers', journal)
        setting_group = 'Identifiers'

    elif display_group == 'crosscheck':
        xref_settings = [
            'enable', 'username', 'password'
        ]

        group_of_settings = process_setting_list(xref_settings, 'crosscheck', journal)
        setting_group = 'crosscheck'

    elif display_group == 'journal':
        journal_settings = [
            'journal_name', 'journal_issn', 'print_issn', 'journal_theme',
            'journal_description', 'main_contact', 'publisher_name',
            'publisher_url', 'contact_info', 'privacy_policy_url', 'auto_signature',
            'slack_logging', 'slack_webhook', 'twitter_handle',
            'switch_language', 'enable_language_text', 'google_analytics_code',
            'use_ga_four', 'display_login_page_notice', 'login_page_notice', 
            'display_register_page_notice', 'register_page_notice',
            'support_email', 'support_contact_message_for_staff',
            'from_address', 'replyto_address',
        ]

        group_of_settings = process_setting_list(journal_settings, 'general', journal)
        group_of_settings[3]['choices'] = get_theme_list()
        setting_group = 'general'

        if group_of_settings[3].get('object').value not in settings.CORE_THEMES:
            group_of_settings.append(
                {
                    'name': 'journal_base_theme',
                    'object': setting_handler.get_setting('general', 'journal_base_theme', journal),
                    'choices': [
                        [theme, theme]
                        for theme in settings.CORE_THEMES]
                },
            )

    elif display_group == 'proofing':
        proofing_settings = [
            'max_proofreaders'
        ]
        group_of_settings = process_setting_list(proofing_settings, 'general', journal)
        setting_group = 'general'
    elif display_group == 'article':
        article_settings = [
            'suppress_how_to_cite',
            'disable_article_thumbnails',
            'disable_article_large_image',
            'display_guest_editors',
            'suppress_citations_metric',
            'display_altmetric_badge',
            'altmetric_badge_type',
            'hide_author_email_links',
            'display_date_submitted',
            'display_date_accepted',
        ]
        group_of_settings = process_setting_list(article_settings, 'article', journal)
        setting_group = 'article'
    elif display_group == 'styling':
        group_of_settings = [
            {
                'name': 'display_journal_title',
                'object': setting_handler.get_setting('styling',
                                                      'display_journal_title',
                                                      journal),
            },
        ]
        setting_group = 'styling'
    elif display_group == 'editorial':
        group_of_settings = [
            {
                'name': 'editorial_group_page_name',
                'object': setting_handler.get_setting('styling',
                                                      'editorial_group_page_name',
                                                      journal),
            },
            {
                'name': 'hide_editorial_group_names',
                'object': setting_handler.get_setting('styling',
                                                      'hide_editorial_group_names',
                                                      journal),
            },
            {
                'name': 'multi_page_editorial',
                'object': setting_handler.get_setting('styling',
                                                      'multi_page_editorial',
                                                      journal),
            },
            {
                'name': 'display_countries_editorial_team',
                'object': setting_handler.get_setting('styling',
                                                      'display_countries_editorial_team',
                                                      journal),
            }
        ]
        setting_group = 'styling'

    elif display_group == 'news':
        group_of_settings = [
            {
                'name': 'news_title',
                'object': setting_handler.get_setting('news', 'news_title', journal),
            },
        ]
        setting_group = 'news'
    else:
        group_of_settings = []
        setting_group = None

    # For each setting check if the current user has permission to
    # edit that setting, otherwise remove it from the group.
    for group_setting_item in group_of_settings[:]:
        if not user_can_edit_setting(
            setting=group_setting_item['object'],
            user=user,
            journal=journal,
        ):
            group_of_settings.remove(group_setting_item)

    return group_of_settings, setting_group


def user_can_edit_setting(setting, user, journal):
    journal_roles = user.roles.get(journal.code) or set()
    setting_editable_roles = setting.editable_by

    # Short circuit for staff users.
    if user.is_staff:
        return True

    # If no roles for the setting are configured we deny access
    # in the event that we want all roles to have access they
    # should be explicitly defined.
    if setting_editable_roles and journal_roles.intersection(setting_editable_roles):
        return True
    return False


def get_theme_list():
    path = os.path.join(settings.BASE_DIR, "themes")
    root, dirs, files = next(os.walk(path))

    return [[dir, dir] for dir in dirs if dir not in ['admin', 'press', '__pycache__']]


def handle_default_thumbnail(request, journal, attr_form):
    if request.FILES.get('default_thumbnail'):
        new_file = files.save_file_to_journal(
            request,
            request.FILES.get('default_thumbnail'),
            'Default Thumb',
            'default',
        )

        if journal.thumbnail_image:
            journal.thumbnail_image.unlink_file(journal=journal)

        journal.thumbnail_image = new_file
        journal.save()

        return new_file

    return None


def article_file(uploaded_file, article, request):
    new_file = files.save_file_to_article(uploaded_file, article, request.user)
    new_file.label = 'Banner image'
    new_file.description = 'Banner image'
    new_file.privacy = 'public'
    new_file.save()
    return new_file


def handle_article_large_image_file(uploaded_file, article, request):
    if not article.large_image_file:
        new_file = article_file(uploaded_file, article, request)

        article.large_image_file = new_file
        article.save()
    else:
        new_file = files.overwrite_file(
                uploaded_file,
                article.large_image_file,
                ('articles', article.pk)
        )
        article.large_image_file = new_file
        article.save()

    resize_and_crop(new_file.self_article_path(), [750, 324], 'middle')


def handle_article_thumb_image_file(uploaded_file, article, request):
    if not article.thumbnail_image_file:
        new_file = article_file(uploaded_file, article, request)

        article.thumbnail_image_file = new_file
        article.save()
    else:
        new_file = files.overwrite_file(
                uploaded_file,
                article.thumbnail_image_file,
                ('articles', article.pk)
        )
        article.thumbnail_image_file = new_file
        article.save()


def handle_email_change(request, email_address):
    request.user.email = email_address
    request.user.is_active = False
    request.user.confirmation_code = uuid.uuid4()
    request.user.clean()
    request.user.save()

    core_confirm_account_url = request.site_type.site_url(
        reverse(
            'core_confirm_account',
            kwargs={'token': request.user.confirmation_code},
        )
    )

    context = {
        'user': request.user,
        'core_confirm_account_url': core_confirm_account_url,
    }
    message = render_template.get_message_content(
        request,
        context,
        'user_email_change',
    )
    notify_helpers.send_email_with_body_from_user(
        request,
        'subject_user_email_change',
        request.user.email,
        message,
    )

    logout(request)


def handle_add_users_to_role(users, role, request):
    role = models.Role.objects.get(pk=role)
    users = models.Account.objects.filter(pk__in=users)

    if not users:
        messages.add_message(request, messages.WARNING, 'No users selected')

    if not role:
        messages.add_message(request, messages.WARNING, 'No role selected.')

    for user in users:
        user.add_account_role(role.slug, request.journal)
        messages.add_message(request, messages.INFO, '{0} added to {1} role.'.format(user.full_name(), role.name))


def clear_active_elements(elements, workflow, plugins):
    elements_to_remove = list()
    for element in elements:
        if workflow.elements.filter(handshake_url=element.get('handshake_url')):
            elements_to_remove.append(element)

    for element in elements_to_remove:
        elements.remove(element)

    return elements


def get_available_elements(workflow):
    plugins = plugin_installed_apps.load_plugin_apps(settings.BASE_DIR)
    our_elements = list()
    elements = models.BASE_ELEMENTS

    for element in elements:
        our_elements.append(element)

    for plugin in plugins:
        try:
            module_name = "{0}.plugin_settings".format(plugin)
            plugin_settings = import_module(module_name)

            if hasattr(plugin_settings, 'IS_WORKFLOW_PLUGIN') and hasattr(
                    plugin_settings, 'HANDSHAKE_URL'):
                if plugin_settings.IS_WORKFLOW_PLUGIN:
                    our_elements.append(
                        {'name': plugin_settings.PLUGIN_NAME,
                         'handshake_url': plugin_settings.HANDSHAKE_URL,
                         'stage': plugin_settings.STAGE,
                         'article_url': plugin_settings.ARTICLE_PK_IN_HANDSHAKE_URL,
                         'jump_url': plugin_settings.JUMP_URL if hasattr(plugin_settings, 'JUMP_URL') else '',
                         }
                    )
        except ImportError as e:
            logger.error(e)

    return clear_active_elements(our_elements, workflow, plugins)


def handle_element_post(workflow, element_name, request):
    for element in get_available_elements(workflow):
        if element['name'] == element_name:
            defaults = {
                'jump_url': element.get('jump_url', ''),
                'stage': element['stage'],
                'handshake_url': element['handshake_url'],

            }
            element_obj, created = models.WorkflowElement.objects.get_or_create(
                journal=request.journal,
                element_name=element_name,
                defaults=defaults,
            )

            return element_obj


def latest_articles(carousel, object_type):
    if object_type == 'journal':
        carousel_objects = submission_models.Article.objects.filter(
            journal=carousel.journal,
            date_published__lte=timezone.now(),
            stage=submission_models.STAGE_PUBLISHED,
        ).order_by("-date_published")
    else:
        carousel_objects = submission_models.Article.objects.filter(
            date_published__lte=timezone.now(),
            stage=submission_models.STAGE_PUBLISHED, ).order_by("-date_published")

    return carousel_objects


def selected_articles(carousel):
    carousel_objects = carousel.articles.all().order_by("-date_published")

    return carousel_objects


def news_items(carousel, object_type, press=None):
    if object_type == 'journal':
        object_id = carousel.journal.pk
    else:
        object_id = carousel.press.pk

    if press and press.carousel_news_items.all():
        return press.carousel_news_items.all()

    carousel_objects = comms_models.NewsItem.objects.filter(
        (Q(content_type__model=object_type) & Q(object_id=object_id)) &
        (Q(start_display__lte=timezone.now()) | Q(start_display=None)) &
        (Q(end_display__gte=timezone.now()) | Q(end_display=None))
    ).order_by('-posted')

    return carousel_objects


def sort_mixed(article_objects, news_objects):
    carousel_objects = []

    for news_item in news_objects:
        for article in article_objects:
            if article.date_published > news_item.posted and article not in carousel_objects:
                    carousel_objects.append(article)
        carousel_objects.append(news_item)

    # add any articles that were not inserted during the above sort procedure
    for article in article_objects:
        if article not in carousel_objects:
            carousel_objects.append(article)

    return carousel_objects


def get_unpinned_articles(request, pinned_articles):
    articles_pinned = [pin.article.pk for pin in pinned_articles]
    return submission_models.Article.objects.filter(journal=request.journal).exclude(pk__in=articles_pinned)


def order_pinned_articles(request, pinned_articles):
    ids = [int(_id) for _id in request.POST.getlist('orders[]')]

    for pin in pinned_articles:
        pin.sequence = ids.index(pin.pk)
        pin.save()


def password_policy_check(request):
    """
    Takes a given string and tests it against the password policy of the press.
    :param request:  HTTPRequest object
    :return: An empty list or a list of errors.
    """
    password = request.POST.get('password_1')

    rules = [
        lambda s: len(password) >= request.press.password_length or _('Your password must be {} characters long').format(request.press.password_length)
    ]

    if request.press.password_upper:
        rules.append(lambda password: any(x.isupper() for x in password) or _('An uppercase character is required'))

    if request.press.password_number:
        rules.append(lambda password: any(x.isdigit() for x in password) or _('A number is required'))

    problems = [p for p in [r(password) for r in rules] if p != True]

    return problems


def get_ua_and_ip(request):
    user_agent = request.META.get('HTTP_USER_AGENT', None)
    ip_address = shared.get_ip_address(request)

    return user_agent, ip_address


def add_failed_login_attempt(request):
    user_agent, ip_address = get_ua_and_ip(request)

    models.LoginAttempt.objects.create(user_agent=user_agent, ip_address=ip_address)


def clear_bad_login_attempts(request):
    user_agent, ip_address = get_ua_and_ip(request)

    models.LoginAttempt.objects.filter(user_agent=user_agent, ip_address=ip_address).delete()


def check_for_bad_login_attempts(request):
    user_agent, ip_address = get_ua_and_ip(request)
    time = timezone.now() - timedelta(minutes=10)

    attempts = models.LoginAttempt.objects.filter(user_agent=user_agent, ip_address=ip_address, timestamp__gte=time)
    print(time, attempts.count())
    return attempts.count()


def handle_file(request, setting_value, file):
    if setting_value.value:
        file_to_delete = models.File.objects.get(pk=setting_value.value)
        files.unlink_journal_file(request, file_to_delete)

    file = files.save_file_to_journal(request, file, setting_value.setting.name, 'A setting file.')
    return file.pk


def no_password_check(username):
    try:
        check = models.Account.objects.get(username=username, password='')
        return check
    except models.Account.DoesNotExist:
        return False


def start_reset_process(request, account):
    # Expire any existing tokens for this user
    models.PasswordResetToken.objects.filter(account=account).update(expired=True)

    # Create a new token
    new_reset_token = models.PasswordResetToken.objects.create(account=account)
    send_reset_token(request, new_reset_token)


def build_submission_list(request):
    section_list = list()
    my_assignments = False
    order = 'pk'

    to_exclude = [
        submission_models.STAGE_PUBLISHED,
        submission_models.STAGE_REJECTED,
        submission_models.STAGE_UNSUBMITTED
    ]

    for key, value in request.POST.items():

        if key.startswith('section_'):
            section_id = re.findall(r'\d+', key)
            if section_id:
                section_list.append(Q(section__pk=section_id[0]))

        elif key.startswith('my_assignments'):
            my_assignments = True
        elif key.startswith('order'):
            order = request.POST.get('order', 'pk')

    if not section_list:
        section_list = [Q(section__pk=section.pk) for section in
                        submission_models.Section.objects.filter(journal=request.journal, is_filterable=True)]

    articles = submission_models.Article.objects.filter(
        journal=request.journal).exclude(
        stage__in=to_exclude
    ).filter(
        reduce(operator.or_, section_list)
    )

    if my_assignments:
        assignments = review_models.EditorAssignment.objects.filter(article__journal=request.journal,
                                                                    editor=request.user)
        assignment_article_pks = [assignment.article.pk for assignment in assignments]
        articles = articles.filter(pk__in=assignment_article_pks)

    return articles.order_by(order)


def create_html_snippet(name, object, template):
    template = get_template(template)
    html_content = template.render({name: object})

    return html_content


def export_gdpr_user_profile(user):
    user = models.Account.objects.get(pk=user.pk)
    user_dict = model_to_dict(user)
    [user_dict.pop(key) for key in
     ['profile_image', 'interest', 'password', 'groups', 'user_permissions', 'activation_code', 'is_superuser',
      'is_staff']]
    response = JsonResponse(user_dict)
    return response


def get_homepage_elements(request):
    homepage_elements = models.HomepageElement.objects.filter(
        content_type=request.model_content_type,
        object_id=request.site_type.pk,
        active=True).order_by('sequence')
    homepage_element_names = [el.name for el in homepage_elements]

    return homepage_elements, homepage_element_names


def render_nested_setting(
        setting_name,
        setting_group,
        request,
        article=None,
        nested_settings=None,
    ):

    setting = setting_handler.get_setting(
        setting_group,
        setting_name,
        request.journal,
    ).processed_value

    setting_context = {}

    if article:
        setting_context['article'] = article

    if not nested_settings:
        nested_settings=[]
    for name, group in nested_settings:
        setting_context[name] = setting_handler.get_setting(
            group,
            name,
            request.journal
        ).processed_value

    rendered_string = render_template.get_message_content(
        request,
        setting_context,
        setting,
        template_is_setting=True
    )

    return rendered_string


def filter_articles_to_editor_assigned(request, articles):
    assignments = review_models.EditorAssignment.objects.filter(
        article__journal=request.journal,
        editor=request.user
    )
    assignment_article_pks = [assignment.article.pk for assignment in assignments]
    return articles.filter(pk__in=assignment_article_pks)
