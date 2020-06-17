from utils import models


class Plugin:
    plugin_name = None
    display_name = None
    description = None
    author = None
    short_name = None
    stage = None

    manager_url = None

    version = None
    janeway_version = None

    is_workflow_plugin = False
    jump_url = None
    handshake_url = None
    article_pk_in_handshake_url = False
    press_wide = False

    kanban_card = '{plugin_name}/kanban_card.html'.format(
        plugin_name=plugin_name,
    )

    @classmethod
    def install(cls):
        plugin, created = cls.get_or_create_plugin_object()

        if not created and plugin.version != cls.version:
            plugin.version = cls.version
            plugin.save()

        return plugin, created

    @classmethod
    def hook_registry(cls):
        pass

    @classmethod
    def get_or_create_plugin_object(cls):
        plugin, created = models.Plugin.objects.get_or_create(
            name=cls.short_name,
            display_name=cls.display_name,
            press_wide=cls.press_wide,
            defaults={'version': cls.version, 'enabled': True},
        )

        return plugin, created
