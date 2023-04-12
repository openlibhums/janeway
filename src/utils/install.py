__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
import json
import os
import codecs

from django.conf import settings
from django.core.files.base import ContentFile

from core import models as core_models
from journal import models
from press import models as press_models
from utils import setting_handler
from submission import models as submission_models
from cms import models as cms_models


def update_settings(journal_object=None, management_command=False,
                    overwrite_with_defaults=False,
                    file_path='utils/install/journal_defaults.json'):
    """ Updates or creates the settings for a journal from journal_defaults.json.

    :param journal_object: the journal object to update or None to set the
        default setting value
    :param management_command: whether to print output to the console
    :return: None
    """
    with codecs.open(os.path.join(settings.BASE_DIR, file_path), encoding='utf-8') as json_data:

        default_data = json.load(json_data)

        for item in default_data:
            setting_group, created = core_models.SettingGroup.objects.get_or_create(
                name=item['group'].get('name'),
            )

            setting_defaults = {
                'types': item['setting'].get('type'),
                'pretty_name': item['setting'].get('pretty_name'),
                'description': item['setting'].get('description'),
                'is_translatable': item['setting'].get('is_translatable')
            }

            setting, created = core_models.Setting.objects.get_or_create(
                name=item['setting'].get('name'),
                group=setting_group,
                defaults=setting_defaults
            )

            if not created:
                for k, v in setting_defaults.items():
                    if not getattr(setting, k) == v:
                        setattr(setting, k, v)
                        setting.save()

            setting_value, created = core_models.SettingValue.objects.get_or_create(
                journal=journal_object,
                setting=setting
            )

            if created or overwrite_with_defaults:
                value = item['value'].get('default')
                if setting.types == 'json' and isinstance(value, (list, dict)):
                    value = json.dumps(value)

                setting_value.value = value
                setting_value.save()

                # clear the many-to-many relationship, mainly for overwrite procedures
                setting.editable_by.clear()
                role_list = item.get('editable_by', None)

                # if no role list is found, default to the status quo
                # where editors and journal-managers can edit a setting
                if not role_list:
                    role_list = ['editor', 'journal-manager']

                roles = core_models.Role.objects.filter(
                    slug__in=role_list,
                )
                setting.editable_by.add(*roles)

            if management_command:
                print('Parsed setting {0}'.format(item['setting'].get('name')))


def load_permissions(file_path='utils/install/journal_defaults.json'):
    with codecs.open(os.path.join(settings.BASE_DIR, file_path), encoding='utf-8') as json_data:
        default_data = json.load(json_data)

        for item in default_data:
            setting_group = core_models.SettingGroup.objects.filter(
                name=item['group'].get('name'),
            ).first()
            setting = core_models.Setting.objects.get(
                name=item['setting'].get('name'),
                group=setting_group,
            )
            role_list = item.get('editable_by', None)

            if role_list:
                roles = core_models.Role.objects.filter(
                    slug__in=role_list,
                )
                setting.editable_by.add(*roles)


def update_emails(journal_object=None, management_command=False):
    """
    Updates email settings with new versions.
    :param journal_object: Journal object or None to set the default setting
        value
    :param management_command: Boolean
    :return: Nothing
    """
    with codecs.open(os.path.join(settings.BASE_DIR, 'utils/install/journal_defaults.json'), encoding='utf-8') as json_data:

        default_data = json.load(json_data)

        for item in default_data:
            group_name = item['group'].get('name')

            if group_name == 'email':

                setting_defaults = {
                    'types': item['setting'].get('type'),
                    'pretty_name': item['setting'].get('pretty_name'),
                    'description': item['setting'].get('description'),
                    'is_translatable': item['setting'].get('is_translatable')
                }

                setting, created = core_models.Setting.objects.get_or_create(
                    name=item['setting'].get('name'),
                    group__name=group_name,
                    defaults=setting_defaults
                )

                setting_value, created = core_models.SettingValue.objects.get_or_create(
                    journal=journal_object,
                    setting=setting
                )

                setting_value.value = item['value'].get('default')
                setting_value.save()

                if management_command:
                    print('{0} Updated'.format(setting.name))


def update_license(journal_object, management_command=False):
    """ Updates or creates the settings for a journal from journal_defaults.json.

    :param journal_object: the journal object to update
    :param management_command: whether to print output to the console
    :return: None
    """
    with codecs.open(os.path.join(settings.BASE_DIR, 'utils/install/licence.json'), encoding='utf-8') as json_data:

        default_data = json.load(json_data)

        for item in default_data:
            default_dict = {
                'name': item['fields'].get('name'),
                'url': item['fields'].get('url'),
                'text': item['fields'].get('text'),
            }
            licence, created = submission_models.Licence.objects.get_or_create(
                journal=journal_object,
                short_name=item['fields'].get('short_name'),
                defaults=default_dict
            )

            if management_command:
                print('Parsed licence {0}'.format(item['fields'].get('short_name')))


def setup_submission_items(journal, manage_command=False):
    with codecs.open(
        os.path.join(
            settings.BASE_DIR,
            'utils/install/submission_items.json'
        )
    ) as json_data:
        submission_items = json.load(json_data)
        for i, setting in enumerate(submission_items):
            if not setting.get('group') == 'special':
                setting_obj = core_models.Setting.objects.get(
                    group__name=setting.get('group'),
                    name=setting.get('name'),
                )
            else:
                setting_obj = None

            obj, c = cms_models.SubmissionItem.objects.get_or_create(
                journal=journal,
                order=i,
                existing_setting=setting_obj,
            )

            setattr(obj, 'title_{}'.format(settings.LANGUAGE_CODE), setting.get('title'))
            obj.save()


def update_xsl_files(journal_object=None, management_command=False):
    with codecs.open(
        os.path.join( settings.BASE_DIR, 'utils/install/xsl_files.json'),
        encoding='utf-8',
    ) as json_data:

        default_data = json.load(json_data)

        for item in default_data:
            file_path = os.path.join(
                settings.BASE_DIR, 'transform/xsl/', item["fields"]["file"])
            with open(file_path, 'rb') as f:
                xsl_file = ContentFile(f.read())
                xsl_file.name = item["fields"]["file"]

            default_dict = {
                'file': xsl_file,
                'comments': item["fields"].get("commments"),
            }
            xsl, created = core_models.XSLFile.objects.get_or_create(
                label=item["fields"]["label"] or settings.DEFAULT_XSL_FILE_LABEL,
                defaults=default_dict,
            )

            if management_command:
                print('Parsed XSL {0}'.format(item['fields'].get('label')))


def update_issue_types(journal_object, management_command=False):
    """ Updates or creates the default issue types for journal

    :param journal_object: the journal object to update
    :param management_command: whether or not to print output to the console
    :return: None
    """
    with codecs.open(
        os.path.join(settings.BASE_DIR, 'utils/install/issue_type.json'),
        encoding='utf-8'
    ) as json_data:
        default_data = json.load(json_data)

        for item in default_data:
            default_dict = {
                'pretty_name': item['fields'].get('pretty_name'),
                'custom_plural': item['fields'].get('custom_plural'),
            }
            issue_type, created = models.IssueType.objects\
            .get_or_create(
                journal=journal_object,
                code=item['fields']['code'],
                defaults=default_dict
            )

            if management_command:
                print('Parsed {0}'.format(issue_type))


def journal(name, code, base_url, delete):
    """ Installs a journal into the system.

    :param name: the name of the new journal
    :param code: the journal's short codename
    :param base_url: the full sub domain at which the journal will reside. E.g. sub domain.domain.org
    :param delete: if true, deletes the journal if it exists
    :return: None
    """

    if delete:
        try:
            models.Journal.objects.get(code=code, domain=base_url).delete()
        except models.Journal.DoesNotExist:
            print('Journal not found, nothing to delete')

    journal_object = models.Journal.objects.create(code=code, domain=base_url)
    update_settings(journal_object, management_command=True)
    setting_handler.save_setting('general', 'journal_name', journal_object, name)
    journal_object.setup_directory()


def press(name, code, domain):
    """ Install the press. Each Janeway instance can host one press with an indefinite number of journals.

    :param name: the name of the press
    :param code: the press's short codename
    :param domain: the domain at which the press resides
    :return: None
    """
    press_models.Press.objects.create(name=name, code=code, domain=domain)
