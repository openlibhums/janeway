import re
from xml.etree import ElementTree as ET

import latex2mathml.converter
import latex2mathml.exceptions

from django import template

register = template.Library()

BLOCK_LATEX_RES = [
    # \[...\]
    re.compile(r"\\\[(?P<value>.+?)\\\]"),
    # $$...$$
    re.compile(r"\$\$(?P<value>.+?)\$\$"),
    # \begin{displaymath}...\end{displaymath}
    re.compile(r"\\begin\{displaymath\}(?P<value>.+?)\\end\{displaymath\}"),
    # \begin{equation}...\end{equation}
    re.compile(r"\\begin\{equation\}(?P<value>.+?)\\end\{equation\}"),
]
INLINE_LATEX_RES = [
    # \(...\)
    re.compile(r"\\\((?P<value>.+?)\\\)"),
    # $...$ but not $$...$$
    re.compile(r"(?<!\$)\$(?!\$)(?P<value>.+?)\$(?!\$)"),
    # \begin{math}...\end{math}
    re.compile(r"\\begin\{math\}(?P<value>.+?)\\end\{math\}"),
]

ET.register_namespace("mml", "http://www.w3.org/1998/Math/MathML")


def _convert(value, display):
    try:
        return latex2mathml.converter.convert(value, display=display)
    except Exception:
        # The input should be returned if there is a parsing error,
        # without delimiters to avoid MathJax attempting to parse it.
        # We don't want MathJax touching TeX syntax because we support $...$ and
        # MathJax does not.
        return value


def _to_html_block(match):
    return _convert(match.group("value"), display="block")


def _to_html_inline(match):
    return _convert(match.group("value"), display="inline")


def _add_mml_namespace_prefix(value):
    xml = ET.fromstring(bytes(value, encoding="utf-8"))
    return ET.tostring(xml, encoding="unicode")


def _to_xml_block(match):
    mathml = _convert(match.group("value"), display="block")
    return _add_mml_namespace_prefix(mathml)


def _to_xml_inline(match):
    mathml = _convert(match.group("value"), display="inline")
    return _add_mml_namespace_prefix(mathml)


def _trim_delimiters(match):
    return match.group("value")


def _should_parse(journal):
    """Whether to parse LaTeX mathematics for this journal"""
    if journal:
        return journal.get_setting("metadata", "latex_mathematics_title_abstract")
    else:
        return False


@register.filter
def to_mathml(value, journal, target="html", allow_block=False):
    assert target in {"xml", "html"}
    if _should_parse(journal):
        if target == "html":
            for pattern in BLOCK_LATEX_RES:
                if allow_block:
                    value = re.sub(pattern, _to_html_block, value)
                else:
                    value = re.sub(pattern, _trim_delimiters, value)
            for pattern in INLINE_LATEX_RES:
                value = re.sub(pattern, _to_html_inline, value)
        elif target == "xml":
            for pattern in BLOCK_LATEX_RES:
                if allow_block:
                    value = re.sub(pattern, _to_xml_block, value)
                else:
                    value = re.sub(pattern, _trim_delimiters, value)
            for pattern in INLINE_LATEX_RES:
                value = re.sub(pattern, _to_xml_inline, value)
    return value


@register.filter
def strip_latex_delimiters(value, journal):
    if _should_parse(journal):
        for pattern in BLOCK_LATEX_RES + INLINE_LATEX_RES:
            value = re.sub(pattern, _trim_delimiters, value)
    return value
