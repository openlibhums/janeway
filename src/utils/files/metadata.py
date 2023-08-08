from libmat2 import parser_factory, UNSUPPORTED_EXTENSIONS
from libmat2 import check_dependencies, UnknownMemberPolicy
import unicodedata
from utils.logger import get_logger
from core.templatetags.truncate import truncatesmart

logger = get_logger(__name__)


def _pretty_meta(metadata, depth=1, ret=None):
    # Ported from 592a0ad93995412b3f88d2effd283a19d911bec2
    padding = "-" * depth * 2
    if ret is None:
        ret = {}

    if not metadata:
        return {"metadata": "No file metadata found."}

    for (k, v) in sorted(metadata.items()):
        if isinstance(v, dict):
            _pretty_meta(v, depth + 1, ret)
            continue
        else:
            try:
                ret[k] = truncatesmart(''.join(
                    ch for ch in v
                    if not unicodedata.category(ch).startswith('C')
                    ), 100)
            except TypeError:
                pass
    return ret


def get_file_metadata(file_path):
    """ Retrieves metadata from file in given path
    :param file_path: A string describing the path to a local file
    """
    # Ported from 592a0ad93995412b3f88d2effd283a19d911bec2
    try:
        parser, _ = parser_factory.get_parser(file_path)
        if parser is not None:
            parser.sandbox = True
            return _pretty_meta(parser.get_meta())
    except ValueError as e:
        logger.error("Error parsing metadata from file %s", article_file)
        logger.exception(e)
    return {}


def scrub_file_metadata(file_path):
    """ Scrubs article metadata in place
    There is no generic File scrubber, because Janeway cannot determine
    the location of a file from its database reprensentation. The file provided
    must be an article file (File.article_id) is set.
    :param file_to_scrub: An instance of core.models.File with article_id set
    :return: The path of the temporary scrubbed file
    """
    try:
        parser, _ = parser_factory.get_parser(file_path)
        if parser is not None:
            parser.sandbox = True
            parser.remove_all()
            return parser.output_filename
    except ValueError as e:
        logger.error("Error parsing metadata from file %s", file_path)
        logger.exception(e)

