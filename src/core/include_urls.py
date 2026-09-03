__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os

from django.urls import include, path, re_path
from django.conf import settings
from django.views.i18n import JavaScriptCatalog
from django.views.decorators.cache import cache_page

from journal import urls as journal_urls
from core import views as core_views, plugin_loader, partial_views
from utils import notify, views as utils_views
from press import views as press_views
from cms import views as cms_views
from submission import views as submission_views
from journal import views as journal_views
from repository import views as repository_views
from utils.logger import get_logger

logger = get_logger(__name__)

urlpatterns = [
    path("", include(journal_urls)),
    path("api/", include("api.urls")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("cms/", include("cms.urls")),
    path("copyediting/", include("copyediting.urls")),
    path("cron/", include("cron.urls")),
    path("discussion/", include("discussion.urls")),
    path("feed/", include("rss.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("identifiers/", include("identifiers.urls")),
    path("install/", include("install.urls")),
    path("metrics/", include("metrics.urls")),
    path("news/", include("comms.urls")),
    path("oidc/", include("mozilla_django_oidc.urls")),
    path("production/", include("production.urls")),
    path("proofing/", include("proofing.urls")),
    path("reports/", include("reports.urls")),
    path("repository/", include("repository.urls")),
    path("review/", include("review.urls")),
    path("rss/", include("rss.urls")),
    path("submit/", include("submission.urls")),
    path("transform/", include("transform.urls")),
    # As part of the typesetting plugin's merge to core we need to support
    # its original url path. Note that the plugin loader will no longer load
    # the typesetting plugin.
    path("plugins/typesetting/", include("typesetting.urls")),
    path("typesetting/", include("typesetting.urls")),
    path("utils/", include("utils.urls")),
    path("workflow/", include("workflow.urls")),
    # Root Site URLS
    path("", press_views.index, name="website_index"),
    path("journals/", press_views.journals, name="press_journals"),
    path("conferences/", press_views.conferences, name="press_conferences"),
    path("kanban/", core_views.kanban, name="kanban"),
    path("login/", core_views.user_login, name="core_login"),
    path("login/orcid/", core_views.user_login_orcid, name="core_login_orcid"),
    path("register/step/1/", core_views.register, name="core_register"),
    path(
        "register/step/1/<uuid:orcid_token>/",
        core_views.register,
        name="core_register_with_orcid_token",
    ),
    re_path(
        r"^register/step/2/(?P<token>[\w-]+)/$",
        core_views.activate_account,
        name="core_confirm_account",
    ),
    re_path(
        r"^register/step/orcid/(?P<token>[\w-]+)/$",
        core_views.orcid_registration,
        name="core_orcid_registration",
    ),
    path("reset/step/1/", core_views.get_reset_token, name="core_get_reset_token"),
    re_path(
        r"^reset/step/2/(?P<token>[\w-]+)/$",
        core_views.reset_password,
        name="core_reset_password",
    ),
    path("profile/", core_views.edit_profile, name="core_edit_profile"),
    path("logout/", core_views.user_logout, name="core_logout"),
    path("dashboard/", core_views.dashboard, name="core_dashboard"),
    path(
        "dashboard/active/",
        core_views.active_submissions,
        name="core_active_submissions",
    ),
    path(
        "dashboard/active/filters/",
        core_views.active_submission_filter,
        name="core_submission_filter",
    ),
    path(
        "dashboard/article/<int:article_id>/",
        core_views.dashboard_article,
        name="core_dashboard_article",
    ),
    path("press/cover/", press_views.serve_press_cover, name="press_cover_download"),
    path(
        "press/file/<int:file_id>/",
        press_views.serve_press_file,
        name="serve_press_file",
    ),
    path(
        "press/user/all/",
        press_views.AllUsers.as_view(),
        name="press_all_users",
    ),
    path("press/merge_users/", press_views.merge_users, name="merge_users"),
    path(
        "doi_manager/",
        press_views.IdentifierManager.as_view(),
        name="press_identifier_manager",
    ),
    path(
        "press/contact/",
        press_views.contact,
        name="press_contact",
    ),
    re_path(
        "press/contact/recipient/(?P<contact_person_id>\d+)/?",
        press_views.contact,
        name="press_contact_with_recipient",
    ),
    # Notes
    path(
        "article/<int:article_id>/note/<int:note_id>/delete/",
        core_views.delete_note,
        name="kanban_delete_note",
    ),
    # Manager URLS
    path("manager/", core_views.manager_index, name="core_manager_index"),
    path(
        "manager/whats_new/",
        core_views.whats_new,
        name="core_manager_whats_new",
    ),
    # Settings Management
    path("manager/settings/", core_views.settings_index, name="core_settings_index"),
    path(
        "manager/default_settings/",
        core_views.default_settings_index,
        name="core_default_settings_index",
    ),
    re_path(
        r"^manager/settings/group/(?P<setting_group>[-\w.: ]+)/setting/(?P<setting_name>[-\w.]+)/$",
        core_views.edit_setting,
        name="core_edit_setting",
    ),
    re_path(
        r"^manager/settings/group/(?P<setting_group>[-\w.: ]+)/default_setting/(?P<setting_name>[-\w.]+)/$",
        core_views.edit_setting,
        name="core_edit_default_setting",
    ),
    re_path(
        r"^manager/settings/(?P<display_group>[-\w.]+)/$",
        core_views.edit_settings_group,
        name="core_edit_settings_group",
    ),
    re_path(
        r"^manager/settings/(?P<plugin>[-\w.:]+)/(?P<setting_group_name>[-\w.]+)/(?P<journal>\d+)/$",
        core_views.edit_plugin_settings_groups,
        name="core_edit_plugin_settings_groups",
    ),
    path(
        "manager/home/settings/",
        core_views.settings_home,
        name="home_settings_index",
    ),
    path(
        "manager/home/settings/order/",
        core_views.journal_home_order,
        name="journal_home_order",
    ),
    # Role Management
    path("manager/roles/", core_views.roles, name="core_manager_roles"),
    re_path(
        r"^manager/roles/(?P<slug>[-\w.]+)/$", core_views.role, name="core_manager_role"
    ),
    re_path(
        r"^manager/roles/(?P<slug>[-\w.]+)/user/(?P<user_id>\d+)/(?P<action>[-\w.]+)/$",
        core_views.role_action,
        name="core_manager_role_action",
    ),
    # Users
    path("manager/user/", core_views.users, name="core_manager_users"),
    path(
        "manager/user/enrol/",
        core_views.enrol_users,
        name="core_manager_enrol_users",
    ),
    path(
        "manager/user/inactive/",
        core_views.inactive_users,
        name="core_manager_inactive_users",
    ),
    path(
        "manager/user/authenticated/",
        core_views.logged_in_users,
        name="core_logged_in_users",
    ),
    path("manager/user/add/", core_views.add_user, name="core_add_user"),
    path(
        "manager/user/<int:user_id>/edit/",
        core_views.user_edit,
        name="core_user_edit",
    ),
    path(
        "manager/user/<int:user_id>/history/",
        core_views.user_history,
        name="core_user_history",
    ),
    # Affiliations
    path(
        "profile/organization/search/",
        core_views.OrganizationListView.as_view(),
        name="core_organization_search",
    ),
    path(
        "profile/organization_name/create/",
        core_views.organization_name_create,
        name="core_organization_name_create",
    ),
    path(
        "profile/organization_name/<int:organization_name_id>/update/",
        core_views.organization_name_update,
        name="core_organization_name_update",
    ),
    path(
        "profile/organization/<int:organization_id>/affiliation/create/",
        core_views.affiliation_create,
        name="core_affiliation_create",
    ),
    path(
        "profile/affiliation/<int:affiliation_id>/update/",
        core_views.affiliation_update,
        name="core_affiliation_update",
    ),
    re_path(
        r"^profile/affiliation/update-from-orcid/(?P<how_many>primary|all)/$",
        core_views.affiliation_update_from_orcid,
        name="core_affiliation_update_from_orcid",
    ),
    path(
        "profile/affiliation/<int:affiliation_id>/delete/",
        core_views.affiliation_delete,
        name="core_affiliation_delete",
    ),
    # Templates
    path("manager/templates/", core_views.email_templates, name="core_email_templates"),
    # Articles Images
    path(
        "manager/article/images/",
        core_views.article_images,
        name="core_article_images",
    ),
    path(
        "manager/article/images/edit/<int:article_pk>/",
        core_views.article_image_edit,
        name="core_article_image_edit",
    ),
    # Contact People
    path(
        "manager/contacts/",
        core_views.contact_people,
        name="core_contact_people",
    ),
    path(
        "manager/contacts/order/",
        core_views.contact_people_reorder,
        name="core_contact_people_reorder",
    ),
    path(
        "manager/contacts/search/",
        core_views.PotentialContactListView.as_view(),
        name="core_contact_person_search",
    ),
    path(
        "manager/contacts/add/<int:account_id>/",
        core_views.contact_person_create,
        name="core_contact_person_create",
    ),
    path(
        "manager/contacts/<int:contact_person_id>/",
        core_views.contact_person_update,
        name="core_contact_person_update",
    ),
    path(
        "manager/contacts/<int:contact_person_id>/delete/",
        core_views.contact_person_delete,
        name="core_contact_person_delete",
    ),
    # Contact messages
    path(
        "manager/contact-messages/",
        utils_views.ContactMessageListView.as_view(),
        name="core_contact_messages",
    ),
    path(
        "manager/contact-messages/<int:log_entry_id>/",
        utils_views.contact_message,
        name="core_contact_message",
    ),
    path(
        "manager/contact-messages/<int:log_entry_id>/delete/",
        utils_views.contact_message_delete,
        name="core_contact_message_delete",
    ),
    # Editorial Team
    path("manager/editorial/", core_views.editorial_team, name="core_editorial_team"),
    path(
        "manager/editorial/<int:group_id>/",
        core_views.edit_editorial_group,
        name="core_edit_editorial_team",
    ),
    path(
        "manager/editorial/new/",
        core_views.edit_editorial_group,
        name="core_add_editorial_team",
    ),
    path(
        "manager/editorial/<int:group_id>/add/",
        core_views.add_member_to_group,
        name="core_editorial_member_to_group",
    ),
    path(
        "manager/editorial/<int:group_id>/add/<int:user_id>/",
        core_views.add_member_to_group,
        name="core_editorial_member_to_group_user",
    ),
    re_path(
        r"^manager/editorial/order/(?P<type_to_order>[-\w.]+)/$",
        core_views.editorial_ordering,
        name="core_editorial_ordering",
    ),
    re_path(
        r"^manager/editorial/order/(?P<type_to_order>[-\w.]+)/group/(?P<group_id>\d+)/$",
        core_views.editorial_ordering,
        name="core_editorial_ordering_group",
    ),
    # Notifications
    path(
        "manager/notifications/",
        core_views.manage_notifications,
        name="core_manager_notifications",
    ),
    path(
        "manager/notifications/<int:notification_id>/",
        core_views.manage_notifications,
        name="core_manager_edit_notifications",
    ),
    # Plugin home
    path("manager/plugins/", core_views.plugin_list, name="core_plugin_list"),
    path("plugins/", core_views.plugin_list, name="core_plugin_list"),
    # Journal Sections
    path("manager/sections/", core_views.section_list, name="core_manager_sections"),
    path(
        "manager/sections/add/",
        core_views.manage_section,
        name="core_manager_section_add",
    ),
    path(
        "manager/sections/<int:section_id>/",
        core_views.manage_section,
        name="core_manager_section",
    ),
    path(
        "manager/sections/<int:section_id>/articles/",
        core_views.section_articles,
        name="core_manager_section_articles",
    ),
    # Pinned Articles
    path(
        "manager/articles/pinned/",
        core_views.pinned_articles,
        name="core_pinned_articles",
    ),
    # Press manager
    path("manager/press/", press_views.edit_press, name="press_edit_press"),
    path(
        "manager/press/journal_order/",
        press_views.journal_order,
        name="press_journal_order",
    ),
    path(
        "manager/press/journal/<int:journal_id>/domain/",
        press_views.journal_domain,
        name="press_journal_domain",
    ),
    path(
        "manager/press/journal/<int:journal_id>/description/",
        press_views.edit_press_journal_description,
        name="edit_press_journal_description",
    ),
    # Workflow
    path("workflow/", core_views.journal_workflow, name="core_journal_workflow"),
    path(
        "workflow/order/",
        core_views.order_workflow_elements,
        name="core_order_workflow_elements",
    ),
    # Cache
    path("manager/cache/flush/", core_views.flush_cache, name="core_flush_cache"),
    path(
        "edit/article/<int:article_id>/metadata/",
        submission_views.edit_metadata,
        name="edit_metadata",
    ),
    path(
        "edit/article/<int:article_id>/author-metadata/",
        submission_views.edit_author_metadata,
        name="submission_edit_author_metadata",
    ),
    path(
        "edit/article/<int:article_id>/current-authors/",
        submission_views.edit_current_authors,
        name="submission_edit_current_authors",
    ),
    path(
        "edit/article/<int:article_id>/authors/order/",
        submission_views.order_authors,
        name="order_authors",
    ),
    # Public Profiles
    re_path(
        r"profile/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/$",
        core_views.public_profile,
        name="core_public_profile",
    ),
    re_path(r"^robots.txt$", press_views.robots, name="website_robots"),
    re_path(r"^sitemap.xml$", press_views.sitemap, name="website_sitemap"),
    # press_views.news_sitemap/pages_sitemap dispatch internally on
    # request.journal/request.repository, so one route each covers press,
    # journal, and repository contexts — no per-site-type name needed.
    re_path(
        r"^news_sitemap.xml$",
        press_views.news_sitemap,
        name="press_news_sitemap",
    ),
    re_path(
        r"^pages_sitemap.xml$",
        press_views.pages_sitemap,
        name="press_pages_sitemap",
    ),
    re_path(
        r"^issue/(?P<issue_id>\d+)_sitemap.xml$",
        journal_views.sitemap,
        name="journal_sitemap",
    ),
    re_path(
        r"^issue/no_issue_sitemap.xml$",
        journal_views.sitemap,
        {"issue_id": "none"},
        name="journal_no_issue_sitemap",
    ),
    re_path(
        r"^subject/(?P<subject_id>\d+)_sitemap.xml$",
        repository_views.sitemap,
        name="repository_sitemap",
    ),
    re_path(
        r"^subject/no_subject_sitemap.xml$",
        repository_views.sitemap,
        {"subject_id": "none"},
        name="repository_no_subject_sitemap",
    ),
    path(
        "download/file/<int:file_id>/",
        journal_views.download_journal_file,
        name="journal_file",
    ),
    path("set-timezone/", core_views.set_session_timezone, name="set_timezone"),
    path(
        "accessibility-mode/toggle/",
        core_views.toggle_accessibility_mode,
        name="toggle_accessibility_mode",
    ),
    path(
        "reading-options/preferences/",
        core_views.save_text_format_preferences,
        name="save_text_format_preferences",
    ),
    path(
        "jsi18n/",
        cache_page(60 * 60, key_prefix="jsi18n_catalog")(JavaScriptCatalog.as_view()),
        name="javascript-catalog",
    ),
    path(
        "permission/submit/",
        core_views.request_submission_access,
        name="request_submission_access",
    ),
    path(
        "permission/requests/",
        core_views.manage_access_requests,
        name="manage_access_requests",
    ),
    # Partial views used for HTMX
    path("alt-text/form/", partial_views.alt_text_form, name="alt_text_form"),
    path("alt-text/submit/", partial_views.alt_text_submit, name="alt_text_submit"),
    path(
        "manager/settings/images/upload/<str:field_name>/",
        partial_views.journal_image_upload,
        name="journal_image_upload",
    ),
    path(
        "manager/settings/images/remove/<str:field_name>/",
        partial_views.journal_image_remove,
        name="journal_image_remove",
    ),
]

# Journal homepage block loading

blocks = plugin_loader.load(
    os.path.join("core", "homepage_elements"),
    prefix="core.homepage_elements",
    permissive=True,
)

if blocks:
    for block in blocks:
        try:
            urlpatterns += [
                re_path(
                    r"^homepage/elements/{0}/".format(block.name),
                    include("core.homepage_elements.{0}.urls".format(block.name)),
                ),
            ]
            logger.debug("Loaded URLs for %s", block.name)
        except ImportError as error:
            logger.warning(
                "Failed to import urls for homepage element %s: %s",
                block.name,
                error,
            )
        except Exception as error:
            logger.error("Error loading homepage element %s", block.name)
            logger.exception(error)

# Plugin Loading
# TODO: plugin_loader should handle the logic below
plugins = plugin_loader.load()

if plugins:
    for plugin in plugins:
        try:
            urlpatterns += [
                re_path(
                    r"^plugins/{0}/".format(plugin.best_name(slug=True)),
                    include("plugins.{0}.urls".format(plugin.name)),
                ),
            ]
            logger.debug("Loaded URLs for %s", plugin.name)
        except ImportError as error:
            logger.warning(
                "Failed to import urls for plugin %s: %s",
                plugin.name,
                error,
            )
        except Exception as error:
            print("Error loading plugin %s", plugin.name)
            logger.error("Error loading plugin %s", plugin.name)
            logger.exception(error)

# load the notification plugins
if len(settings.NOTIFY_FUNCS) == 0:
    plugins = notify.load_modules()
    frameworks = []

    for key, val in plugins.items():
        if hasattr(val, "notify_hook"):
            settings.NOTIFY_FUNCS.append(val.notify_hook)

urlpatterns += [
    re_path(r"^site/(?P<page_name>.*)/$", cms_views.view_page, name="cms_page"),
]
