from events import logic as events_logic
from utils import plugins
from utils.install import update_settings

PLUGIN_NAME = 'Typesetting Plugin'
DISPLAY_NAME = 'Typesetting'
DESCRIPTION = 'An alternative for Production/Proofing'
AUTHOR = 'Andy Byers'
VERSION = '0.2'
SHORT_NAME = 'typesetting'
MANAGER_URL = 'typesetting_manager'
JANEWAY_VERSION = "1.3.7"

# Workflow Settings
IS_WORKFLOW_PLUGIN = True
HANDSHAKE_URL = 'typesetting_article'
ARTICLE_PK_IN_HANDSHAKE_URL = True
STAGE = 'typesetting_plugin'

ON_TYPESETTING_COMPLETE = "on_typesetting_complete"


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
    TypesettingPlugin.hook_registry()

def register_for_events():
    # Plugin modules can't be imported until plugin is loaded
    from plugins.typesetting.notifications import emails
    events_logic.Events.register_for_event(
        events_logic.Events.ON_REVIEWER_REQUESTED_ACKNOWLEDGE,
        emails.send_typesetting_complete
    )
