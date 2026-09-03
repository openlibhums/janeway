import os
import shutil
import boto3
import subprocess
from io import StringIO

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail

from core import models


def copy_file(source, destination):
    """
    :param source: The source of the folder for copying
    :param destination: The destination folder for the file
    :return:
    """

    destination_folder = os.path.join(settings.BASE_DIR, os.path.dirname(destination))

    if not os.path.exists(destination_folder):
        os.mkdir(destination_folder)

    print("Copying {0}".format(source))
    shutil.copy(
        os.path.join(settings.BASE_DIR, source),
        os.path.join(settings.BASE_DIR, destination),
    )


def copy_files(src_path, dest_path):
    """
    :param src_path: The source folder for copying
    :param dest_path: The destination these files/folders should be copied to
    :return: None
    """
    if not os.path.exists(src_path):
        os.makedirs(src_path)

    files = os.listdir(src_path)

    for file_name in files:
        if not file_name == "temp":
            full_file_name = os.path.join(src_path, file_name)
            print("Copying {0}".format(full_file_name))
            if os.path.isfile(full_file_name):
                shutil.copy(full_file_name, dest_path)
            else:
                dir_dest = os.path.join(dest_path, file_name)
                if os.path.exists(dir_dest):
                    shutil.rmtree(os.path.join(dir_dest))
                shutil.copytree(full_file_name, dir_dest)


def mycb(bytes_transferred):
    # boto3's Callback only receives the number of bytes transferred so far
    # for this invocation of the callback (not a running total or the file
    # size), unlike boto2's cb(so_far, total). We just report the chunk size
    # transferred rather than reconstructing a running total/percentage.
    print("{0} kb transferred".format(bytes_transferred / 1024))


def handle_s3(tmp_path, start_time):
    print("Sending to S3.")
    file_name = "{0}.zip".format(start_time)
    file_path = os.path.join(settings.BASE_DIR, "files", "temp", file_name)
    f = open(file_path, "rb")

    END_POINT = settings.END_POINT
    S3_HOST = settings.S3_HOST
    UPLOADED_FILENAME = "backups/{0}.zip".format(start_time)
    # include folders in file path. If it doesn't exist, it will be created

    # END_POINT is an AWS region name (e.g. "eu-west-2") and S3_HOST is that
    # region's S3 endpoint hostname (e.g. "s3.eu-west-2.amazonaws.com") -- see
    # the documented defaults in janeway_global_settings.py. boto3 derives the
    # correct endpoint from region_name on its own, but we still pass
    # S3_HOST through as endpoint_url so a deployment that has customised
    # S3_HOST to point elsewhere (e.g. an S3-compatible non-AWS host) keeps
    # working exactly as it did with boto2's `host=` kwarg.
    s3 = boto3.client(
        "s3",
        region_name=END_POINT,
        endpoint_url="https://{0}".format(S3_HOST),
        aws_access_key_id=settings.S3_ACCESS_KEY,
        aws_secret_access_key=settings.S3_SECRET_KEY,
    )

    s3.upload_fileobj(
        f,
        settings.S3_BUCKET_NAME,
        UPLOADED_FILENAME,
        Callback=mycb,
    )


def handle_directory(tmp_path, start_time):
    print("Copying to backup dir")
    file_name = "{0}.zip".format(start_time)
    copy_file("files/temp/{0}".format(file_name), settings.BACKUP_DIR)


def delete_used_tmp(tmp_path, start_time):
    print("Deleting temp directory.")
    shutil.rmtree(tmp_path)
    file_path = "{0}/{1}.zip".format(
        os.path.join(settings.BASE_DIR, "files", "temp"), start_time
    )
    os.unlink(file_path)


def send_email(start_time, e, success=False):
    admins = models.Account.objects.filter(is_superuser=True)
    message = ""

    if not success:
        message = "There was an error during the backup process.\n\n "

    send_mail(
        "Backup",
        "{0}{1}.".format(message, e),
        "backup@janeway",
        [user.email for user in admins],
        fail_silently=False,
    )


class Command(BaseCommand):
    """
    Pulls files together then sends them to aws bucket.
    """

    help = "Deletes duplicate settings."

    def handle(self, *args, **options):
        """Does a backup..

        :param args: None
        :param options: None
        :return: None
        """

        # Ensure temp dir exists:
        if not os.path.exists(os.path.join(settings.BASE_DIR, "files", "temp")):
            os.makedirs(os.path.join(settings.BASE_DIR, "files", "temp"))

        start_time = str(timezone.now())
        try:
            tmp_path = os.path.join(settings.BASE_DIR, "files", "temp", start_time)

            # dump database out to JSON and store in StringIO for saving
            print("Dumping json db file")
            json_out = StringIO()
            call_command(
                "dumpdata",
                "--indent=4",
                "--natural-foreign",
                "--exclude=contenttypes",
                stdout=json_out,
            )

            write_path = os.path.join(
                settings.BASE_DIR, "files", "temp", "janeway.json"
            )
            with open(write_path, "w", encoding="utf-8") as write:
                json_out.seek(0)
                shutil.copyfileobj(json_out, write)

            os.mkdir(tmp_path)
            copy_file(
                "files/temp/janeway.json",
                "files/temp/{0}/janeway.json".format(start_time),
            )
            copy_files(
                os.path.join(settings.BASE_DIR, "media"),
                os.path.join(tmp_path, "media"),
            )
            copy_files(
                os.path.join(settings.BASE_DIR, "files"),
                os.path.join(tmp_path, "files"),
            )
            print("Creating archive.")
            shutil.make_archive(
                os.path.join(settings.BASE_DIR, "files", "temp", start_time),
                "zip",
                tmp_path,
            )

            if settings.BACKUP_TYPE == "s3":
                handle_s3(tmp_path, start_time)
            else:
                handle_directory(tmp_path, start_time)
            delete_used_tmp(tmp_path, start_time)

            if settings.BACKUP_EMAIL:
                send_email(start_time, "Backup was successfully completed.")
        except Exception as e:
            send_email(start_time, e)
