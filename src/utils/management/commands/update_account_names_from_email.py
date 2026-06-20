from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.db import models

import csv
from core import models as core_models
from utils.logger import get_logger


logger = get_logger(__name__)


class Command(BaseCommand):
    """Update the first and last name of matching accounts from CSV."""

    help = "Update the first and last name of matching accounts from CSV."

    def add_arguments(self, parser):
        parser.add_argument("input_file")
        parser.add_argument("--email_column_heading", default="Author email")
        parser.add_argument("--first_name_column_heading", default="Author given name")
        parser.add_argument("--last_name_column_heading", default="Author surname")
        parser.add_argument("--encoding", default="utf-8")
        parser.add_argument(
            "-d",
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
        )

    def handle(self, *args, **options):
        input_file_path = options["input_file"]
        email_heading = options["email_column_heading"]
        first_name_heading = options["first_name_column_heading"]
        last_name_heading = options["last_name_column_heading"]
        encoding = options["encoding"]
        dry_run = options["dry_run"]

        with open(input_file_path, "r", encoding=encoding) as reader_file:
            reader = csv.DictReader(reader_file)
            ending = "_dry_run_result.csv" if dry_run else "_result.csv"
            output_file_path = input_file_path.replace(".csv", ending)
            with open(output_file_path, "w", encoding=encoding) as writer_file:
                fieldnames = [
                    email_heading,
                    "Matching error",
                    first_name_heading,
                    first_name_heading + " updated from",
                    last_name_heading,
                    last_name_heading + " updated from",
                ]
                writer = csv.DictWriter(writer_file, fieldnames=fieldnames)
                writer.writeheader()
                for i, row in enumerate(tqdm(reader)):
                    csv_email = row[email_heading]
                    first_name = row[first_name_heading]
                    last_name = row[last_name_heading]

                    # Do the same preparation as Account.clean()
                    email = core_models.Account.objects.normalize_email(csv_email)
                    username = csv_email.lower()

                    row_result = {}
                    matching_accounts = core_models.Account.objects.filter(
                        models.Q(email__iexact=email)
                        | models.Q(username__iexact=username),
                    )
                    if matching_accounts.count() == 0:
                        row_result[email_heading] = email
                        row_result["Matching error"] = "Not found"
                        writer.writerow(row_result)
                        continue
                    if matching_accounts.count() >= 2:
                        row_result[email_heading] = email
                        row_result["Matching error"] = "Found multiple"
                        writer.writerow(row_result)
                        continue
                    account = matching_accounts[0]
                    updated = False
                    if account.first_name != first_name:
                        row_result[first_name_heading] = first_name
                        row_result[first_name_heading + " updated from"] = (
                            account.first_name
                        )
                        account.first_name = first_name
                        updated = True
                    if account.last_name != last_name:
                        row_result[last_name_heading] = last_name
                        row_result[last_name_heading + " updated from"] = (
                            account.last_name
                        )
                        account.last_name = last_name
                        updated = True
                    if updated:
                        row_result[email_heading] = email
                        if not dry_run:
                            account.save()
                        writer.writerow(row_result)
