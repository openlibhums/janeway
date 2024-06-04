from events import logic as events_logic
from utils import plugins
from utils.install import update_settings

PLUGIN_NAME = 'Typesetting Plugin'
DISPLAY_NAME = 'Typesetting'
DESCRIPTION = 'An alternative for Production/Proofing'
AUTHOR = 'Birkbeck Centre for Technology and Publishing'
VERSION = '1.6'
SHORT_NAME = 'typesetting'
MANAGER_URL = 'typesetting_manager'
JANEWAY_VERSION = '1.6.0'

# Workflow Settings
IS_WORKFLOW_PLUGIN = True
JUMP_URL = 'typesetting_article'
HANDSHAKE_URL = 'typesetting_articles'
ARTICLE_PK_IN_HANDSHAKE_URL = True
STAGE = 'typesetting_plugin'
KANBAN_CARD = 'typesetting/elements/card.html'
DASHBOARD_TEMPLATE = 'typesetting/elements/dashboard.html'

ON_TYPESETTING_COMPLETE = "on_typesetting_complete"
ON_TYPESETTING_ASSIGN_NOTIFICATION = "on_typesetting_assign_notification"
ON_TYPESETTING_ASSIGN_DECISION = "on_typesetting_assign_decision"
ON_TYPESETTING_ASSIGN_CANCELLED = "on_typesetting_assign_cancelled"
ON_TYPESETTING_ASSIGN_DELETED = "on_typesetting_assign_deleted"
ON_TYPESETTING_ASSIGN_COMPLETE = "on_typesetting_assign_complete"
ON_PROOFREADER_ASSIGN_NOTIFICATION = "on_proofreader_assign_notification"
ON_PROOFREADER_ASSIGN_CANCELLED = "on_proofreader_assign_cancelled"
ON_PROOFREADER_ASSIGN_RESET = "on_proofreader_assign_reset"
ON_PROOFREADER_ASSIGN_COMPLETE = "on_proofreader_assign_complete"


class TypesettingPlugin(plugins.Plugin):
    plugin_name = PLUGIN_NAME
    display_name = DISPLAY_NAME
    description = DESCRIPTION
    author = AUTHOR
    short_name = SHORT_NAME
    stage = STAGE

    manager_url = MANAGER_URL

    version = VERSION
    janeway_version = JANEWAY_VERSION

    is_workflow_plugin = IS_WORKFLOW_PLUGIN
    handshake_url = HANDSHAKE_URL
    article_pk_in_handshake_url = ARTICLE_PK_IN_HANDSHAKE_URL


def install():
    TypesettingPlugin.install()
    update_settings(
        file_path='plugins/typesetting/install/settings.json'
    )


def hook_registry():
    return {
        'core_article_tasks':
            {
                'module': 'plugins.typesetting.hooks',
                'function': 'author_tasks',
            },
    }


def register_for_events():
    # Plugin modules can't be imported until plugin is loaded
    from plugins.typesetting.notifications import emails

    events_logic.Events.register_for_event(
        ON_TYPESETTING_ASSIGN_NOTIFICATION,
        emails.send_typesetting_assign_notification,
    )

    events_logic.Events.register_for_event(
        ON_TYPESETTING_ASSIGN_DECISION,
        emails.send_typesetting_assign_decision,
    )

    events_logic.Events.register_for_event(
        ON_TYPESETTING_ASSIGN_CANCELLED,
        emails.send_typesetting_assign_cancelled,
    )

    events_logic.Events.register_for_event(
        ON_TYPESETTING_ASSIGN_DELETED,
        emails.send_typesetting_assign_deleted,
    )

    events_logic.Events.register_for_event(
        ON_TYPESETTING_ASSIGN_COMPLETE,
        emails.send_typesetting_assign_complete,
    )

    events_logic.Events.register_for_event(
        ON_PROOFREADER_ASSIGN_NOTIFICATION,
        emails.send_proofreader_assign_notification,
    )

    events_logic.Events.register_for_event(
        ON_PROOFREADER_ASSIGN_CANCELLED,
        emails.send_proofreader_assign_transaction_email,
    )

    events_logic.Events.register_for_event(
        ON_PROOFREADER_ASSIGN_RESET,
        emails.send_proofreader_assign_transaction_email,
    )

    events_logic.Events.register_for_event(
        ON_PROOFREADER_ASSIGN_COMPLETE,
        emails.send_proofreader_assign_transaction_email,
    )

    events_logic.Events.register_for_event(
        ON_TYPESETTING_COMPLETE,
        emails.send_typesetting_complete,
    )
