from django.db import migrations
from django.db.models import OuterRef, Subquery


def populate_field_answer_field_name(apps, schema_editor):
    Field = apps.get_model("submission", "Field")
    FieldAnswer = apps.get_model("submission", "FieldAnswer")
    FieldAnswer.objects.filter(field__isnull=False).update(
        field_name=Subquery(
            Field.objects.filter(pk=OuterRef("field_id")).values("name")[:1]
        ),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("submission", "0090_fieldanswer_field_name"),
    ]

    operations = [
        migrations.RunPython(
            populate_field_answer_field_name,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
