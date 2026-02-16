import json
import os

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    """Updates Accessibility Conformance markdown from JSON."""

    help = "This will overwrite the conformance markdown file."

    # Conformance symbol mapping
    conformance_symbol_map = {
        "Not-applicable": ":brown_square:",
        "Partially Supports": ":orange_circle:",
        "Supports": ":white_check_mark:",
        "Does not support": ":x:",
    }

    def add_arguments(self, parser):
        """Adds arguments to Django's management command-line parser.

        :param parser: the parser to which the required arguments will be added
        :return: None
        """
        parser.add_argument(
            "--json-file",
            type=str,
            default=os.path.join(
                settings.BASE_DIR,
                "..",
                "docs",
                "md",
                "a11y",
                "conformance_data.json",
            ),
            help="Path to the JSON data file",
        )
        parser.add_argument(
            "--output",
            type=str,
            default=os.path.join(
                settings.BASE_DIR,
                "..",
                "docs",
                "md",
                "a11y",
                "a11y_conformance.md",
            ),
            help="Path to the output markdown file",
        )

    def format_table_cell(self, value):
        """Format a table cell value, handling None and empty strings."""
        if value is None:
            return ""
        return str(value)

    def output_table_row(self, row_data):
        """Output a markdown table row."""
        return (
            f"| {row_data['result']:<20} | {row_data['criterion_text']:<60} | {row_data['level']:<5} | "
            f"{row_data['conformance']:<18} | {row_data['remarks']:<7} | {row_data['audit']:<20} |"
        )

    def generate_table_row(self, criterion_id, area_criterion_data):
        """Generate a markdown table row for a criterion.

        Args:
            criterion_id: The criterion ID (e.g., "1.1.1")
            area_criterion_data: The criterion data from the area (contains conformance, remarks, audit)
        """
        # Look up the full criterion info from the top-level criteria
        criterion_info = self.data["criteria"].get(criterion_id, {})
        criterion_name = criterion_info.get("criterion_name", "")
        level = criterion_info.get("level", "")

        conformance = area_criterion_data.get("conformance")
        conformance_symbol = ""
        if conformance and conformance in self.conformance_symbol_map:
            conformance_symbol = self.conformance_symbol_map[conformance]

        row_data = {
            "result": self.format_table_cell(conformance_symbol),
            "criterion_text": f"{criterion_id} {criterion_name}",
            "level": self.format_table_cell(level),
            "conformance": self.format_table_cell(conformance),
            "remarks": self.format_table_cell(area_criterion_data.get("remarks")),
            "audit": self.format_table_cell(area_criterion_data.get("audit")),
        }
        return self.output_table_row(row_data)

    def generate_area_table(self, area_data):
        """Generate a markdown table for an area."""

        # Column headings
        headings = {
            "result": "Result",
            "criterion_text": "Success Criterion",
            "level": "Level",
            "conformance": "Conformance",
            "remarks": "Remarks",
            "audit": "Audit",
        }
        lines = [self.output_table_row(headings)]
        lines.append("|---" * len(headings) + "|")

        audit_results = area_data.get("audit_results", {})

        # Iterate over all criteria from the top-level criteria object
        # Sort by criterion ID to ensure consistent ordering
        for criterion_id in sorted(self.data["criteria"].keys()):
            # Get area-specific data for this criterion, or use empty dict if not present
            result_data = audit_results.get(criterion_id, {})
            lines.append(self.generate_table_row(criterion_id, result_data))

        return "\n".join(lines)

    def handle(self, *args, **options):
        """Generates conformance markdown from JSON data file.

        :param args: None
        :param options: Command options
        :return: None
        """
        json_file = options.get("json_file")
        output_file = options.get("output")

        # Resolve and normalize paths
        json_file = os.path.normpath(os.path.abspath(json_file))
        output_file = os.path.normpath(os.path.abspath(output_file))

        # Load JSON data
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"JSON file not found: {json_file}"))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f"Invalid JSON file: {e}"))
            return

        # Generate markdown
        lines = []

        # Title
        lines.append(f"# {self.data['metadata']['title']}")
        lines.append("")
        lines.append(self.data["metadata"]["description"])
        lines.append("")

        # Results Key
        lines.append("## Results Key")
        lines.append("")
        lines.append("| Result | Markdown Symbol |")
        lines.append("|---|---|")
        for result, symbol in self.conformance_symbol_map.items():
            lines.append(f"| {result} | {symbol} `{symbol}` |")
        lines.append("")

        # Generate tables for each area
        for area_key in self.data["area"]:
            if area_key in self.data["area"]:
                area_data = self.data["area"][area_key]
                area_name = area_data["name"]
                lines.append(f"## {area_name}")
                lines.append("")
                # Handle notes if they exist
                notes = area_data.get("notes", [])
                if notes:
                    for note in notes:
                        lines.append(note)
                    lines.append("")
                # Generate table if results exist
                if "audit_results" in area_data:
                    lines.append(self.generate_area_table(area_data))
                    lines.append("")

        # Write output
        try:
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)

            with open(output_file, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully generated VPAT markdown: {output_file}"
                )
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error writing output file: {e}"))
