__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

import os

from django.conf.urls import include, url
from django.conf import settings
from django.views.i18n import JavaScriptCatalog
from django.views.decorators.cache import cache_page

from journal import urls as journal_urls
from core import views as core_views, plugin_loader
from utils import notify
from press import views as press_views
from cms import views as cms_views
from submission import views as submission_views
from journal import views as journal_views
from utils.logger import get_logger

logger = get_logger(__name__)

urlpatterns = [
    url(r'^submit/', include('submission.urls')),
    url(r'^', include(journal_urls)),
    url(r'^review/', include('review.urls')),
    url(r'^metrics/', include('metrics.urls')),
    url(r'^identifiers/', include('identifiers.urls')),
    url(r'^production/', include('production.urls')),
    url(r'^proofing/', include('proofing.urls')),
    url(r'^cms/', include('cms.urls')),
    url(r'^transform/', include('transform.urls')),
    url(r'^copyediting/', include('copyediting.urls')),
    url(r'^rss/', include('rss.urls')),
    url(r'^feed/', include('rss.urls')),
    url(r'^cron/', include('cron.urls')),
    url(r'^install/', include('install.urls')),
    url(r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^api/', include('api.urls')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^news/', include('comms.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^repository/', include('repository.urls')),
    url(r'^utils/', include('utils.urls')),
    url(r'^workflow/', include('workflow.urls')),
    url(r'^discussion/', include('discussion.urls')),
    url('oidc/', include('mozilla_django_oidc.urls')),

    # Root Site URLS
    url(r'^$', press_views.index, name='website_index'),
    url(r'^journals/$', press_views.journals, name='press_journals'),
    url(r'^article_list/$', core_views.FilteredArticlesListView.as_view(), name='article_list'),
    url(r'^conferences/$', press_views.conferences, name='press_conferences'),
    url(r'^kanban/$', core_views.kanban, name='kanban'),
    url(r'^login/$', core_views.user_login, name='core_login'),
    url(r'^login/orcid/$', core_views.user_login_orcid, name='core_login_orcid'),
    url(r'^register/step/1/$', core_views.register, name='core_register'),
    url(r'^register/step/2/(?P<token>[\w-]+)/$', core_views.activate_account, name='core_confirm_account'),
    url(r'^register/step/orcid/(?P<token>[\w-]+)/$', core_views.orcid_registration, name='core_orcid_registration'),
    url(r'^reset/step/1/$', core_views.get_reset_token, name='core_get_reset_token'),
    url(r'^reset/step/2/(?P<token>[\w-]+)/$', core_views.reset_password, name='core_reset_password'),
    url(r'^profile/$', core_views.edit_profile, name='core_edit_profile'),
    url(r'^logout/$', core_views.user_logout, name='core_logout'),
    url(r'^dashboard/$', core_views.dashboard, name='core_dashboard'),
    url(r'^dashboard/active/$', core_views.active_submissions, name='core_active_submissions'),
    url(r'^dashboard/active/filters/$', core_views.active_submission_filter, name='core_submission_filter'),
    url(r'^dashboard/article/(?P<article_id>\d+)/$', core_views.dashboard_article, name='core_dashboard_article'),

    url(r'^press/cover/$', press_views.serve_press_cover, name='press_cover_download'),
    url(r'^press/file/(?P<file_id>\d+)/$',
        press_views.serve_press_file,
        name='serve_press_file',
        ),
    url(r'^press/merge_users/$', press_views.merge_users, name='merge_users'),
    url(r'^doi_manager/$', press_views.IdentifierManager.as_view(), name='press_identifier_manager'),

    # Notes
    url(r'^article/(?P<article_id>\d+)/note/(?P<note_id>\d+)/delete/$', core_views.delete_note,
        name='kanban_delete_note'),

    # Manager URLS
    url(r'^manager/$', core_views.manager_index, name='core_manager_index'),

    # Settings Management
    url(r'^manager/settings/$', core_views.settings_index, name='core_settings_index'),
    url(r'^manager/default_settings/$', core_views.default_settings_index, name='core_default_settings_index'),
    url(r'^manager/settings/group/(?P<setting_group>[-\w.: ]+)/setting/(?P<setting_name>[-\w.]+)/$',
        core_views.edit_setting,
        name='core_edit_setting'),
    url(r'^manager/settings/group/(?P<setting_group>[-\w.: ]+)/default_setting/(?P<setting_name>[-\w.]+)/$',
        core_views.edit_setting,
        name='core_edit_default_setting'),
    url(r'^manager/settings/(?P<display_group>[-\w.]+)/$', core_views.edit_settings_group, name='core_edit_settings_group'),
    url(r'^manager/settings/(?P<plugin>[-\w.:]+)/(?P<setting_group_name>[-\w.]+)/(?P<journal>\d+)/$',
        core_views.edit_plugin_settings_groups, name='core_edit_plugin_settings_groups'),

    url(r'^manager/home/settings/$', core_views.settings_home, name='home_settings_index'),
    url(r'^manager/home/settings/order/$', core_views.journal_home_order, name='journal_home_order'),

    # Role Management
    url(r'^manager/roles/$', core_views.roles, name='core_manager_roles'),
    url(r'^manager/roles/(?P<slug>[-\w.]+)/$', core_views.role, name='core_manager_role'),
    url(r'^manager/roles/(?P<slug>[-\w.]+)/user/(?P<user_id>\d+)/(?P<action>[-\w.]+)/$', core_views.role_action,
        name='core_manager_role_action'),

    # Users
    url(r'^manager/user/$', core_views.users, name='core_manager_users'),
    url(r'^manager/user/enrol/$', core_views.enrol_users, name='core_manager_enrol_users'),
    url(r'^manager/user/inactive/$', core_views.inactive_users, name='core_manager_inactive_users'),
    url(r'^manager/user/authenticated/$', core_views.logged_in_users, name='core_logged_in_users'),
    url(r'^manager/user/add/$', core_views.add_user, name='core_add_user'),
    url(r'^manager/user/(?P<user_id>\d+)/edit/$', core_views.user_edit, name='core_user_edit'),
    url(r'^manager/user/(?P<user_id>\d+)/history/$', core_views.user_history, name='core_user_history'),

    # Templates
    url(r'^manager/templates/$', core_views.email_templates, name='core_email_templates'),

    # Articles Images
    url(r'^manager/article/images/$', core_views.article_images, name='core_article_images'),
    url(r'^manager/article/images/edit/(?P<article_pk>\d+)/$', core_views.article_image_edit,
        name='core_article_image_edit'),

    # Journal Contacts
    url(r'^manager/contacts/$', core_views.contacts, name='core_journal_contacts'),
    url(r'^manager/contacts/add/$', core_views.edit_contacts, name='core_new_journal_contact'),
    url(r'^manager/contacts/(?P<contact_id>\d+)/$', core_views.edit_contacts, name='core_journal_contact'),
    url(r'^manager/contacts/order/$', core_views.contacts_order, name='core_journal_contacts_order'),

    # Editorial Team
    url(r'^manager/editorial/$', core_views.editorial_team, name='core_editorial_team'),
    url(r'^manager/editorial/(?P<group_id>\d+)/$', core_views.edit_editorial_group,
        name='core_edit_editorial_team'),
    url(r'^manager/editorial/new/$', core_views.edit_editorial_group,
        name='core_add_editorial_team'),
    url(r'^manager/editorial/(?P<group_id>\d+)/add/$', core_views.add_member_to_group,
        name='core_editorial_member_to_group'),
    url(r'^manager/editorial/(?P<group_id>\d+)/add/(?P<user_id>\d+)/$', core_views.add_member_to_group,
        name='core_editorial_member_to_group_user'),
    url(r'^manager/editorial/order/(?P<type_to_order>[-\w.]+)/$',
        core_views.editorial_ordering,
        name='core_editorial_ordering'),
    url(r'^manager/editorial/order/(?P<type_to_order>[-\w.]+)/group/(?P<group_id>\d+)/$',
        core_views.editorial_ordering,
        name='core_editorial_ordering_group'),

    # Notifications
    url(r'^manager/notifications/$',
        core_views.manage_notifications, name='core_manager_notifications'),
    url(r'^manager/notifications/(?P<notification_id>\d+)/$',
        core_views.manage_notifications, name='core_manager_edit_notifications'),

    # Plugin home
    url(r'^manager/plugins/$',
        core_views.plugin_list,
        name='core_plugin_list'),

    # Journal Sections
    url(r'^manager/sections/$',
        core_views.section_list, name='core_manager_sections'),
    url(r'^manager/sections/add/$',
        core_views.manage_section, name='core_manager_section_add'),
    url(r'^manager/sections/(?P<section_id>\d+)/$',
        core_views.manage_section, name='core_manager_section'),
    url(r'^manager/sections/(?P<section_id>\d+)/articles/$',
        core_views.section_articles, name='core_manager_section_articles'),

    # Pinned Articles
    url(r'^manager/articles/pinned/$',
        core_views.pinned_articles, name='core_pinned_articles'),

    # Press manager
    url(r'^manager/press/$',
        press_views.edit_press,
        name='press_edit_press'),
    url(r'^manager/press/journal_order/$',
        press_views.journal_order,
        name='press_journal_order'),
    url(r'^manager/press/journal/(?P<journal_id>\d+)/domain/$',
        press_views.journal_domain,
        name='press_journal_domain'),
    url(r'^manager/press/journal/(?P<journal_id>\d+)/description/$',
        press_views.edit_press_journal_description,
        name='edit_press_journal_description'),

    # Workflow
    url(r'^workflow/$',
        core_views.journal_workflow,
        name='core_journal_workflow'),
    url(r'^workflow/order/$',
        core_views.order_workflow_elements,
        name='core_order_workflow_elements'),

    # Cache
    url(r'^manager/cache/flush/$', core_views.flush_cache, name='core_flush_cache'),

    url(r'^edit/article/(?P<article_id>\d+)/metadata/$', submission_views.edit_metadata, name='edit_metadata'),
    url(r'^edit/article/(?P<article_id>\d+)/authors/order/$', submission_views.order_authors, name='order_authors'),

    # Public Profiles
    url(r'profile/(?P<uuid>[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12})/$', core_views.public_profile, name='core_public_profile'),

    url(r'^robots.txt$', press_views.robots, name='website_robots'),
    url(r'^sitemap.xml$', press_views.sitemap, name='website_sitemap'),
    url(r'^(?P<issue_id>\d+)_sitemap.xml$', journal_views.sitemap, name='website_sitemap'),

    url(r'^download/file/(?P<file_id>\d+)/$', journal_views.download_journal_file, name='journal_file'),

    url(r'^set-timezone/$', core_views.set_session_timezone, name='set_timezone'),

    url(r'^jsi18n/$', cache_page(60 * 60, key_prefix='jsi18n_catalog')(JavaScriptCatalog.as_view()), name='javascript-catalog'),
    url(r'permission/submit/$', core_views.request_submission_access, name='request_submission_access'),
    url(r'permission/requests/$', core_views.manage_access_requests, name='manage_access_requests'),
]

# Journal homepage block loading

blocks = plugin_loader.load(
    os.path.join('core', 'homepage_elements'),
    prefix='core.homepage_elements',
    permissive=True,
)

if blocks:
    for block in blocks:
        try:
            urlpatterns += [
                url(
                    r'^homepage/elements/{0}/'.format(block.name),
                    include(
                        'core.homepage_elements.{0}.urls'.format(block.name))
                ),
            ]
            logger.debug("Loaded URLs for %s", block.name)
        except ImportError as error:
            logger.warning(
                "Failed to import urls for homepage element %s: %s",
                block.name, error,
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
                url(
                    r'^plugins/{0}/'.format(plugin.best_name(slug=True)),
                    include('plugins.{0}.urls'.format(plugin.name))
                ),
            ]
            logger.debug("Loaded URLs for %s", plugin.name)

        except ImportError as error:
            logger.warning(
                "Failed to import urls for plugin %s: %s", plugin.name, error,
            )
        except Exception as error:
            logger.error("Error loading plugin %s", block.name)
            logger.exception(error)

# load the notification plugins
if len(settings.NOTIFY_FUNCS) == 0:
    plugins = notify.load_modules()
    frameworks = []

    for key, val in plugins.items():
        if hasattr(val, 'notify_hook'):
            settings.NOTIFY_FUNCS.append(val.notify_hook)

urlpatterns += [
    url(r'^site/(?P<page_name>.*)/$', cms_views.view_page, name='cms_page'),
]
