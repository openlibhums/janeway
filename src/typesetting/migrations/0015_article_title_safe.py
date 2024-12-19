# Written on Jun 12 2024

from django.db import migrations
from utils import migration_utils


EMAILS_WITH_RAW_ARTICLE_TITLES = [
    (
        'typesetting_notify_typesetter',
        '<p>Dear {{ assignment.typesetter.full_name }},</p><p>This is a notification from {{ request.user.full_name }} that you have been assigned to the production of article {{ assignment.round.article.title }} on journal {{ request.journal.name }}. </p><p>You can view further information on this assignment: {{ typesetting_assignments_url }}.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    ),
    (
        'typesetting_notify_proofreader',
        '<p>Dear {{ assignment.proofreader.full_name }},</p><p>This is an notification from {{ request.user.full_name }} that you have been assigned to proofread {{ assignment.round.article.title }} on journal {{ request.journal.name }}. </p><p>You can view further information on this assignment: {{ typesetting_assignments_url }}.</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    ),
    (
        'typesetting_complete',
        '<p>Dear editors,</p><p>This is an automatic notification to inform you that Typesetting is complete for article \"{{ article.title}}\".</p><p>Regards,</p><p>{{ request.user.signature|safe }}</p>',
    ),
    (
        'typesetting_proofreader_completed',
        '<p>Dear {{assignment.manager.full_name}},</p><p>This is a notification to let you know that the proofing you requested for the article {{assignment.round.article.title}}, with article number {{assignment.round.article.pk}}, has now been completed by {{assignment.proofreader.full_name}}.</p><p>Best wishes,</p>',
    ),
    (
        'typesetting_proofreader_cancelled',
        '<p>Dear {{assignment.proofreader.full_name}},</p><p>This is a notification to let you know that your proofreading request for the article {{assignment.round.article.title}}, with article number {{assignment.round.article.pk}} has been cancelled. This means that you no longer need to complete this proofreading task</p><p>Best wishes,</p><p>{{ assignment.manager.signature|safe }}</p>',
    ),
    (
        'typesetting_proofreader_reset',
        '<p>Dear {{assignment.proofreader.full_name}},</p><p>This is a notification to let you know that your proofreading request for the article {{assignment.round.article.title}}, with article number {{assignment.round.article.pk}}, has been reopened. Please log in to the journal using this link in order to complete this proofreading request: {{ typesetting_proofreading_assignments }}.</p><p>Thank you for your help,</p><p>Best wishes,</p><p>{{ assignment.manager.signature|safe }}</p>',
    ),
    (
        'typesetting_typesetter_cancelled',
        '<p>Dear {{assignment.proofreader.full_name}},</p><p>This is a notification to let you know that your typesetting request for the article {{assignment.round.article.title}}, with article number {{assignment.round.article.pk}}, has been cancelled. This means that you no longer need to complete this task.</p><p>Thank you for your help,</p><p>{{ assignment.manager.signature|safe }}</p>',
    ),
    (
        'typesetting_typesetter_deleted',
        '<p>Dear {{assignment.proofreader.full_name}},</p><p>This is a notification to let you know that your typesetting request for the article {{assignment.round.article.title}}, with article number {{assignment.round.article.pk}}, has been deleted. This means that you no longer need to complete this task.</p><p>Thank you for your help,</p><p>{{ assignment.manager.signature|safe }}</p>',
    ),
]


def use_safe_article_title_in_setting_values(apps, schema_editor):
    for setting_name, old_value in EMAILS_WITH_RAW_ARTICLE_TITLES:
        new_value = old_value.replace('article.title', 'article.safe_title')
        migration_utils.update_default_setting_values(
            apps,
            setting_name,
            'email',
            values_to_replace=[old_value],
            replacement_value=new_value,
        )


class Migration(migrations.Migration):

    dependencies = [
        ('typesetting', '0014_alter_galleyproofing_manager'),
    ]

    operations = [
        migrations.RunPython(
            use_safe_article_title_in_setting_values,
            reverse_code=migrations.RunPython.noop,
        )
    ]
