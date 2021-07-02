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
            print('Plugin updated: {0} -> {1}'.format(cls.version, plugin.version))
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
            defaults={
                'display_name': cls.display_name,
                'version': cls.version,
                'enabled': True,
                'press_wide': cls.press_wide,
            },
        )

        return plugin, created

    @classmethod
    def get_self(cls):
        try:
            plugin = models.Plugin.objects.get(
                name=cls.short_name,
            )
        except models.Plugin.MultipleObjectsReturned:
            plugin = models.Plugin.objects.filter(
                name=cls.short_name,
            ).order_by(
                '-version'
            ).first()
        except models.Plugin.DoesNotExist:
            return None

        return plugin
