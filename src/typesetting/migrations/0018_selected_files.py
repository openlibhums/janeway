from django.db import migrations, models


def select_expected_files(apps, schema_editor):
    TypesettingAssignment = apps.get_model('typesetting', 'TypesettingAssignment')
    TypesettingRound = apps.get_model('typesetting', 'TypesettingRound')
    File = apps.get_model('core', 'File')
    for assignment in TypesettingAssignment.objects.exclude(
        round__article__stage='Archived',
    ):
        article = assignment.round.article

        data_figure_files = File.objects.filter(
            data_figure_files=article,
        )
        for file in data_figure_files:
            assignment.files_to_typeset.add(file)

        galley_files = File.objects.filter(
            galley__article=article,
        )
        for file in galley_files:
            assignment.files_to_typeset.add(file)

        rounds = TypesettingRound.objects.filter(article=article)
        if rounds.count() > 1:
            previous_round = rounds[1]
        else:
            previous_round = None
        if previous_round and assignment.display_proof_comments:
            proofing_files = File.objects.filter(
                galleyproofing__round__article=article,
                galleyproofing__round=previous_round,
                galleyproofing__completed__isnull=False,
            )
            for file in proofing_files:
                assignment.files_to_typeset.add(file)


class Migration(migrations.Migration):

    dependencies = [
        ('typesetting', '0017_auto_20240708_1727'),
    ]

    operations = [
        migrations.RunPython(
            select_expected_files,
            reverse_code=migrations.RunPython.noop
        ),
    ]
