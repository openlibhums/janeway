from django import template

from core import files

register = template.Library()


@register.simple_tag
def file_metadata_scrubbing_enabled():
    try:
        from utils.files import metadata as file_metadata
        return True
    except (ModuleNotFoundError, ImportError):
        return False


def get_article_file_metadata(article_file):
    metadata = {}
    try:
        metadata = get_article_file_metadata(article_file)
    except ValueError:
        pass
    return metadata

