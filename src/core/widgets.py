from django.forms import ClearableFileInput, CheckboxSelectMultiple, Select


class JanewayFileInput(ClearableFileInput):
    template_name = "admin/core/widgets/janeway_clearable_file.html"


class TableMultiSelectUser(CheckboxSelectMultiple):
    template_name = "admin/core/widgets/multi_checkbox_user_table.html"


class OptGroupSelect(Select):
    """Select widget that renders choices in <optgroup> elements.

    Set groups to a dict of {group_name: set_of_values}. Options with no
    value (empty/placeholder) are always rendered ungrouped at the top.
    Options not found in any group are rendered in a final ungrouped set.

    Example input dict:
        {
            "Assigned to this article": {3, 7},
            "Other editors": {1, 2, 4, 5, 6, 8},
        }

    Example usage in a form __init__:
        assigned_pks = {e.pk for e in assigned_editors}
        other_pks = {e.pk for e in all_editors if e.pk not in assigned_pks}
        self.fields["editor"].widget.groups = {
            "Assigned to this article": assigned_pks,
            "Other editors": other_pks,
        }
    """

    def __init__(self, *args, groups=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups = groups or {}

    def optgroups(self, name, value, attrs=None):
        buckets = {group_name: [] for group_name in self.groups}
        empty = []
        ungrouped = []

        for index, (option_value, option_label) in enumerate(self.choices):
            option = self.create_option(
                name,
                option_value,
                option_label,
                str(option_value) in value,
                index,
                attrs=attrs,
            )
            if not option_value:
                empty.append(option)
            else:
                matched = next(
                    (g for g, pks in self.groups.items() if option_value in pks),
                    None,
                )
                if matched:
                    buckets[matched].append(option)
                else:
                    ungrouped.append(option)

        result = []
        if empty:
            result.append(("", empty, 0))
        for i, (group_name, options) in enumerate(buckets.items(), start=1):
            if options:
                result.append((group_name, options, i))
        if ungrouped:
            result.append(("", ungrouped, len(result) + 1))
        return result
