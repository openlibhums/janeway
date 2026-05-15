from django.db import migrations


EDITOR_ASSIGNMENT_NAME = "editor_assignment"
LEGACY_HANDSHAKE_URL = "review_unassigned"
LEGACY_JUMP_URL = "review_unassigned_article"
PRIMARY_HANDSHAKE_URL = "editor_assignment_list"
PRIMARY_JUMP_URL = "editor_assignment_article"


def use_primary_urls(apps, schema_editor):
    """Update existing editor_assignment WorkflowElement rows to use the new
    canonical URL names. Legacy URL names continue to resolve via the
    backward-compat patterns in review.urls."""
    WorkflowElement = apps.get_model("core", "WorkflowElement")
    WorkflowElement.objects.filter(
        element_name=EDITOR_ASSIGNMENT_NAME,
    ).update(
        handshake_url=PRIMARY_HANDSHAKE_URL,
        jump_url=PRIMARY_JUMP_URL,
    )


def use_legacy_urls(apps, schema_editor):
    """Revert editor_assignment WorkflowElement rows to the pre-bau#271
    URL names."""
    WorkflowElement = apps.get_model("core", "WorkflowElement")
    WorkflowElement.objects.filter(
        element_name=EDITOR_ASSIGNMENT_NAME,
    ).update(
        handshake_url=LEGACY_HANDSHAKE_URL,
        jump_url=LEGACY_JUMP_URL,
    )


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0111_editor_assignment_workflow_element"),
    ]

    operations = [
        migrations.RunPython(
            use_primary_urls,
            reverse_code=use_legacy_urls,
        ),
    ]
