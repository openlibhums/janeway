__copyright__ = "Copyright 2026 Birkbeck, University of London"
__author__ = "Open Library of Humanities"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"

"""
Regression coverage for utils.management.commands.backup.

Originally written ahead of the boto (v2) -> boto3 migration (Phase 1 of the
Django 5.2 migration plan) so we had a "before" baseline that exercised the
S3 upload path without touching the network. Prior to that, `backup` had
zero dedicated test coverage - the only "backup" hit in the old
utils/tests.py module was an unrelated code comment.

Updated in Phase 2 (the actual boto -> boto3 migration) to mock the boto3
call sites (boto3.client("s3", ...).upload_fileobj(...)) instead of boto2's
connect_to_region()/Key. The behavioural assertions (bucket name, key naming
under "backups/...", email-on-success/failure) are unchanged.
"""

import shutil
import tempfile
from unittest.mock import MagicMock, patch

from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings

from utils.testing import helpers


def _fake_dumpdata(command_name, *args, **kwargs):
    """
    Stand-in for `call_command("dumpdata", ...)` as invoked inside
    utils.management.commands.backup.

    Under the sqlite settings this whole suite runs with, a real dumpdata
    run fails with "no such table: core_pgfiletext" because
    core.models.PGFileText declares `required_db_vendor = "postgresql"`
    and so has no table on sqlite, even though dumpdata still tries to
    serialize it. That is a pre-existing sqlite/postgres model
    incompatibility, unrelated to the S3 upload path this test targets, so
    the dumpdata step is faked out here rather than worked around.
    """
    assert command_name == "dumpdata"
    stdout = kwargs.get("stdout")
    if stdout is not None:
        stdout.write("[]")


@override_settings(
    BACKUP_TYPE="s3",
    BACKUP_EMAIL=True,
    S3_ACCESS_KEY="test-access-key",
    S3_SECRET_KEY="test-secret-key",
    S3_BUCKET_NAME="test-bucket",
    S3_HOST="s3.eu-west-2.amazonaws.com",
    END_POINT="eu-west-2",
)
class BackupCommandS3Test(TestCase):
    """
    Exercises `manage.py backup` end to end with BACKUP_TYPE="s3", mocking
    only the boto (v2) network layer so the real dumpdata/zip/cleanup logic
    still runs against a throwaway BASE_DIR.
    """

    @classmethod
    def setUpTestData(cls):
        # send_email() queries Account.objects.filter(is_superuser=True)
        # to build the recipient list.
        cls.superuser = helpers.create_user(
            "backup-admin@example.org",
            is_superuser=True,
            is_active=True,
        )

    def setUp(self):
        # The command reads/writes settings.BASE_DIR/files and
        # settings.BASE_DIR/media directly, so give it a scratch directory
        # rather than touching the real checkout.
        self.tmp_base_dir = tempfile.mkdtemp(prefix="janeway-backup-test-")
        self.addCleanup(shutil.rmtree, self.tmp_base_dir, ignore_errors=True)
        self.override = override_settings(BASE_DIR=self.tmp_base_dir)
        self.override.enable()
        self.addCleanup(self.override.disable)

    @patch("utils.management.commands.backup.call_command", side_effect=_fake_dumpdata)
    @patch("utils.management.commands.backup.boto3.client")
    def test_backup_uploads_to_s3_and_emails_superusers(
        self, mock_boto3_client, mock_call_command
    ):
        mock_s3_client = MagicMock()
        mock_boto3_client.return_value = mock_s3_client

        call_command("backup")

        # The command created an S3 client for the configured region/host
        # with the configured credentials rather than making a real AWS
        # call.
        mock_boto3_client.assert_called_once_with(
            "s3",
            region_name="eu-west-2",
            endpoint_url="https://s3.eu-west-2.amazonaws.com",
            aws_access_key_id="test-access-key",
            aws_secret_access_key="test-secret-key",
        )

        # The backup archive was uploaded to the configured bucket under a
        # "backups/...zip" key.
        mock_s3_client.upload_fileobj.assert_called_once()
        args, kwargs = mock_s3_client.upload_fileobj.call_args
        _, bucket_name, uploaded_key = args
        self.assertEqual(bucket_name, "test-bucket")
        self.assertTrue(uploaded_key.endswith(".zip"))
        self.assertTrue(uploaded_key.startswith("backups/"))

        # BACKUP_EMAIL=True, so a completion email should have been sent to
        # every superuser account.
        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn(self.superuser.email, sent.to)
        self.assertEqual(sent.subject, "Backup")
        self.assertIn("successfully completed", sent.body)

    @patch("utils.management.commands.backup.call_command", side_effect=_fake_dumpdata)
    @patch("utils.management.commands.backup.boto3.client")
    def test_backup_emails_superusers_on_s3_failure(
        self, mock_boto3_client, mock_call_command
    ):
        # Simulate a failure talking to S3 (e.g. auth error / network issue)
        # and confirm the command does not raise, but instead reports the
        # error by email, per its except/send_email() logic.
        mock_boto3_client.side_effect = Exception("boom: could not connect")

        call_command("backup")

        mock_boto3_client.assert_called_once()

        self.assertEqual(len(mail.outbox), 1)
        sent = mail.outbox[0]
        self.assertIn(self.superuser.email, sent.to)
        self.assertEqual(sent.subject, "Backup")
        self.assertIn("There was an error during the backup process", sent.body)
        self.assertIn("boom: could not connect", sent.body)
