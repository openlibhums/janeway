import os
from pathlib import Path
import subprocess
import shutil
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

from utils.logger import get_logger


logger = get_logger(__name__)

PROJECT_ROOT = Path(settings.BASE_DIR).parent


def no_src(path):
    if path.startswith("src/templates/"):
        path = path[14:]
    return path


class Command(BaseCommand):
    """
    Creates a template checklist for a given search term.

    Can be used in development to identify changes to make across the templates.

    Example usage:

python src/manage.py create_template_checklist \
"success|alert|danger|delete|error|warning|callout|badge" \
--invert_match="button_delete" \
--write
    """

    def add_arguments(self, parser):
        parser.add_argument("pattern")
        parser.add_argument("--output", default="template_checklist.md")
        parser.add_argument("--invert_match")
        parser.add_argument("--write", action="store_true", default=False)
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        executable = "rg"
        if not shutil.which(executable):
            logger.warning("The rg executable was not found.")
            return
        pattern = options.get("pattern")
        search_path = "src/templates"
        invert_match = options.get("invert_match")
        output = options.get("output")
        write = options.get("write")
        env = {
            "RIPGREP_CONFIG_PATH": ".ripgrep_config",
        }
        process = subprocess.run(
            [executable, pattern, search_path],
            capture_output=True,
            encoding="utf-8",
            cwd=PROJECT_ROOT,
            env=env,
        )

        if invert_match:
            process = subprocess.run(
                [executable, "--invert-match", invert_match],
                input=process.stdout,
                capture_output=True,
                encoding="utf-8",
                cwd=PROJECT_ROOT,
                env=env,
            )

        results = {}
        if os.path.isfile(output):
            with open(output, "r") as fileref:
                file_lines = list(fileref.readlines())
        else:
            file_lines = []
        for line in file_lines:
            if not line.startswith("- ["):
                continue
            result = line[7:-2]
            is_complete = line.startswith("- [x]")
            if is_complete:
                # Don't include the pre-existing result if it has not been ticked off
                results[result] = is_complete
        if not write:
            logger.info(f"Not showing {len(results)} existing results in {output}.")
        list_count = len(results)
        for result in process.stdout.split("\n"):
            if result and result not in results and no_src(result) not in results:
                list_count += 1
                is_complete = False
                results[result] = is_complete
                if not write:
                    print(result)

        checklist = "# To do\n\n"

        # The arg values received from the interpreter are strings, with internal
        # quotation escaping removed, so we need to add that back in for the
        # markdown file to have a copy-pastable line.

        # e.g. python src/manage.py create_template_checklist
        args = f"python {sys.argv[0]} {sys.argv[1]}"

        # e.g. warning|error
        search_string = sys.argv[2]

        # e.g. invert_match=include "warning.html"
        args += f' "{search_string}"'
        for kwarg in sys.argv[3:]:
            if "=" in kwarg:
                subj, obj = kwarg.split("=", maxsplit=1)
                obj = obj.replace('"', '\\"')
                kwarg = f'{subj}="{obj}"'
            args += " " + kwarg
        checklist += f"This list was created with this command:\n{args}\n\n"

        for result, is_complete in sorted(results.items()):
            checklist += f"- [{'x' if is_complete else ' '}] `{no_src(result)}`\n"
        if write:
            with open(output, "w") as fileref:
                fileref.write(checklist)
        if list_count:
            logger.info(f"Results: {list_count}")
