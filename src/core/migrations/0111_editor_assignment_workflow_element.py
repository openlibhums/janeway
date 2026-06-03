from django.db import migrations


EDITOR_ASSIGNMENT_NAME = "editor_assignment"
EDITOR_ASSIGNMENT_HANDSHAKE_URL = "review_unassigned"
EDITOR_ASSIGNMENT_JUMP_URL = "review_unassigned_article"
REVIEW_NAME = "review"
STAGE_UNASSIGNED = "Unassigned"
STAGE_ASSIGNED = "Assigned"


def insert_editor_assignment(apps, schema_editor):
    """For every Workflow, add an Editor Assignment element at the front and
    realign the existing Review element to STAGE_ASSIGNED."""
    Workflow = apps.get_model("core", "Workflow")
    WorkflowElement = apps.get_model("core", "WorkflowElement")

    for workflow in Workflow.objects.all():
        existing = list(workflow.elements.order_by("order", "element_name"))
        # Bump existing element orders to make room at position 0.
        for index, element in enumerate(existing, start=1):
            if element.order != index:
                element.order = index
                element.save()

        # Narrow the legacy "review" element so it no longer owns STAGE_UNASSIGNED.
        for element in existing:
            if (
                element.element_name == REVIEW_NAME
                and element.stage == STAGE_UNASSIGNED
            ):
                element.stage = STAGE_ASSIGNED
                element.save()

        new_element, _ = WorkflowElement.objects.get_or_create(
            journal=workflow.journal,
            element_name=EDITOR_ASSIGNMENT_NAME,
            defaults={
                "handshake_url": EDITOR_ASSIGNMENT_HANDSHAKE_URL,
                "jump_url": EDITOR_ASSIGNMENT_JUMP_URL,
                "stage": STAGE_UNASSIGNED,
                "article_url": True,
                "order": 0,
            },
        )
        # Ensure the element's URLs and order are correct even if it pre-existed.
        new_element.handshake_url = EDITOR_ASSIGNMENT_HANDSHAKE_URL
        new_element.jump_url = EDITOR_ASSIGNMENT_JUMP_URL
        new_element.stage = STAGE_UNASSIGNED
        new_element.article_url = True
        new_element.order = 0
        new_element.save()

        workflow.elements.add(new_element)


def remove_editor_assignment(apps, schema_editor):
    """Reverse migration: detach editor_assignment from every Workflow,
    restore the Review element's stage to STAGE_UNASSIGNED, and delete the
    orphaned WorkflowElement rows. WorkflowLog history for the removed
    elements is cascaded by the FK and is not recoverable."""
    Workflow = apps.get_model("core", "Workflow")
    WorkflowElement = apps.get_model("core", "WorkflowElement")

    for workflow in Workflow.objects.all():
        elements = workflow.elements.filter(element_name=EDITOR_ASSIGNMENT_NAME)
        for element in elements:
            workflow.elements.remove(element)

        for element in workflow.elements.filter(
            element_name=REVIEW_NAME,
            stage=STAGE_ASSIGNED,
        ):
            element.stage = STAGE_UNASSIGNED
            element.save()

    WorkflowElement.objects.filter(element_name=EDITOR_ASSIGNMENT_NAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0110_alttext"),
    ]

    operations = [
        migrations.RunPython(
            insert_editor_assignment,
            reverse_code=remove_editor_assignment,
        ),
    ]
