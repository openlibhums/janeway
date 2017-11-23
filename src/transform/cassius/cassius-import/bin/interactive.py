#!/usr/bin/env python
from __future__ import print_function
__author__ = "Martin Paul Eve"
__email__ = "martin@martineve.com"

"""
A class to handle an interactive prompt.

Portions of this file are Copyright 2014, Adrian Sampson.
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

"""
from debug import Debuggable
import sys
from difflib import SequenceMatcher
import locale


class Interactive(Debuggable):
    def __init__(self, debug):
        self.debug = debug
        Debuggable.__init__(self, 'Interactive Prompt Handler')

        # ANSI terminal colorization code heavily inspired by pygments:
        # http://dev.pocoo.org/hg/pygments-main/file/b2deea5b5030/pygments/console.py
        # (pygments is by Tim Hatch, Armin Ronacher, et al.)
        self.COLOR_ESCAPE = "\x1b["
        self.DARK_COLORS = ["black", "darkred", "darkgreen", "brown", "darkblue",
                            "purple", "teal", "lightgray"]
        self.LIGHT_COLORS = ["darkgray", "red", "green", "yellow", "blue",
                             "fuchsia", "turquoise", "white"]
        self.RESET_COLOR = self.COLOR_ESCAPE + "39;49;00m"

    def input_options(self, options, require=False, prompt=None, fallback_prompt=None,
                      numrange=None, default=None, max_width=72):
        """Prompts a user for input. The sequence of `options` defines the
        choices the user has. A single-letter shortcut is inferred for each
        option; the user's choice is returned as that single, lower-case
        letter. The options should be provided as lower-case strings unless
        a particular shortcut is desired; in that case, only that letter
        should be capitalized.

        By default, the first option is the default. `default` can be provided to
        override this. If `require` is provided, then there is no default. The
        prompt and fallback prompt are also inferred but can be overridden.

        If numrange is provided, it is a pair of `(high, low)` (both ints)
        indicating that, in addition to `options`, the user may enter an
        integer in that inclusive range.

        `max_width` specifies the maximum number of columns in the
        automatically generated prompt string.
        """
        # Assign single letters to each option. Also capitalize the options
        # to indicate the letter.
        letters = {}
        display_letters = []
        capitalized = []
        first = True
        for option in options:
            # Is a letter already capitalized?
            for letter in option:
                if letter.isalpha() and letter.upper() == letter:
                    found_letter = letter
                    break
            else:
                # Infer a letter.
                for letter in option:
                    if not letter.isalpha():
                        continue  # Don't use punctuation.
                    if letter not in letters:
                        found_letter = letter
                        break
                else:
                    raise ValueError('no unambiguous lettering found')

            letters[found_letter.lower()] = option
            index = option.index(found_letter)

            # Mark the option's shortcut letter for display.
            if not require and ((default is None and not numrange and first) or
                                (isinstance(default, basestring) and
                                 found_letter.lower() == default.lower())):
                # The first option is the default; mark it.
                show_letter = '[%s]' % found_letter.upper()
                is_default = True
            else:
                show_letter = found_letter.upper()
                is_default = False

            # Colorize the letter shortcut.
            show_letter = self.colorize('green' if is_default else 'red',
                                        show_letter)

            # Insert the highlighted letter back into the word.
            capitalized.append(
                option[:index] + show_letter + option[index + 1:]
            )
            display_letters.append(found_letter.upper())

            first = False

        # The default is just the first option if unspecified.
        if require:
            default = None
        elif default is None:
            if numrange:
                default = numrange[0]
            else:
                default = display_letters[0].lower()

        # Make a prompt if one is not provided.
        if not prompt:
            prompt_parts = []
            prompt_part_lengths = []
            if numrange:
                if isinstance(default, int):
                    default_name = str(default)
                    default_name = self.colorize('turquoise', default_name)
                    tmpl = '# selection (default %s)'
                    prompt_parts.append(tmpl % default_name)
                    prompt_part_lengths.append(len(tmpl % str(default)))
                else:
                    prompt_parts.append('# selection')
                    prompt_part_lengths.append(len(prompt_parts[-1]))
            prompt_parts += capitalized
            prompt_part_lengths += [len(s) for s in options]

            # Wrap the query text.
            prompt = ''
            line_length = 0
            for i, (part, length) in enumerate(zip(prompt_parts,
                                                   prompt_part_lengths)):
                # Add punctuation.
                if i == len(prompt_parts) - 1:
                    part += '?'
                else:
                    part += ','
                length += 1

                # Choose either the current line or the beginning of the next.
                if line_length + length + 1 > max_width:
                    prompt += '\n'
                    line_length = 0

                if line_length != 0:
                    # Not the beginning of the line; need a space.
                    part = ' ' + part
                    length += 1

                prompt += part
                line_length += length

        # Make a fallback prompt too. This is displayed if the user enters
        # something that is not recognized.
        if not fallback_prompt:
            fallback_prompt = 'Enter one of '
            if numrange:
                fallback_prompt += '%i-%i, ' % numrange
            fallback_prompt += ', '.join(display_letters) + ':'

        resp = self.input_(prompt)
        while True:
            resp = resp.strip().lower()

            # Try default option.
            if default is not None and not resp:
                resp = default

            # Try an integer input if available.
            if numrange:
                try:
                    resp = int(resp)
                except ValueError:
                    pass
                else:
                    low, high = numrange
                    if low <= resp <= high:
                        return resp
                    else:
                        resp = None

            # Try a normal letter input.
            if resp:
                resp = resp[0]
                if resp in letters:
                    return resp

            # Prompt for new input.
            resp = self.input_(fallback_prompt)

    def input_(self, prompt=None):
        """Like `raw_input`, but decodes the result to a Unicode string.
        Raises a UserError if stdin is not available. The prompt is sent to
        stdout rather than stderr. A printed between the prompt and the
        input cursor.
        """
        # raw_input incorrectly sends prompts to stderr, not stdout, so we
        # use print() explicitly to display prompts.
        # http://bugs.python.org/issue1927
        if prompt:
            if isinstance(prompt, unicode):
                prompt = prompt.encode(self._encoding(), 'replace')
            print(prompt, end=' ')

        try:
            resp = raw_input()
        except EOFError:
            self.debug.print_debug('stdin stream ended while input required')

        return resp.decode(sys.stdin.encoding or 'utf8', 'ignore')

    def _encoding(self):
        """Tries to guess the encoding used by the terminal."""
        # Determine from locale settings.
        try:
            return locale.getdefaultlocale()[1] or 'utf8'
        except ValueError:
            # Invalid locale environment variable setting. To avoid
            # failing entirely for no good reason, assume UTF-8.
            return 'utf8'

    def _colorize(self, color, text):
        """Returns a string that prints the given text in the given color
        in a terminal that is ANSI color-aware. The color must be something
        in DARK_COLORS or LIGHT_COLORS.
        """
        if color in self.DARK_COLORS:
            escape = self.COLOR_ESCAPE + "%im" % (self.DARK_COLORS.index(color) + 30)
        elif color in self.LIGHT_COLORS:
            escape = self.COLOR_ESCAPE + "%i;01m" % (self.LIGHT_COLORS.index(color) + 30)
        else:
            raise ValueError('no such color %s', color)
        return escape + text + self.RESET_COLOR

    def colorize(self, color, text):
        """Colorize text if colored output is enabled. (Like _colorize but
        conditional.)
        """
        return self._colorize(color, text)

    def _colordiff(self, a, b, highlight='red', minor_highlight='lightgray'):
        """Given two values, return the same pair of strings except with
        their differences highlighted in the specified color. Strings are
        highlighted intelligently to show differences; other values are
        stringified and highlighted in their entirety.
        """
        if not isinstance(a, basestring) or not isinstance(b, basestring):
            # Non-strings: use ordinary equality.
            a = unicode(a)
            b = unicode(b)
            if a == b:
                return a, b
            else:
                return self.colorize(highlight, a), self.colorize(highlight, b)

        if isinstance(a, bytes) or isinstance(b, bytes):
            # A path field.
            a = self.displayable_path(a)
            b = self.displayable_path(b)

        a_out = []
        b_out = []

        matcher = SequenceMatcher(lambda x: False, a, b)
        for op, a_start, a_end, b_start, b_end in matcher.get_opcodes():
            if op == 'equal':
                # In both strings.
                a_out.append(a[a_start:a_end])
                b_out.append(b[b_start:b_end])
            elif op == 'insert':
                # Right only.
                b_out.append(self.colorize(highlight, b[b_start:b_end]))
            elif op == 'delete':
                # Left only.
                a_out.append(self.colorize(highlight, a[a_start:a_end]))
            elif op == 'replace':
                # Right and left differ. Colorise with second highlight if
                # it's just a case change.
                if a[a_start:a_end].lower() != b[b_start:b_end].lower():
                    color = highlight
                else:
                    color = minor_highlight
                a_out.append(self.colorize(color, a[a_start:a_end]))
                b_out.append(self.colorize(color, b[b_start:b_end]))
            else:
                assert(False)

        return u''.join(a_out), u''.join(b_out)

    def displayable_path(self, path, separator=u'; '):
        """Attempts to decode a bytestring path to a unicode object for the
        purpose of displaying it to the user. If the `path` argument is a
        list or a tuple, the elements are joined with `separator`.
        """
        if isinstance(path, (list, tuple)):
            return separator.join(self.displayable_path(p) for p in path)
        elif isinstance(path, unicode):
            return path
        elif not isinstance(path, str):
            # A non-string object: just get its unicode representation.
            return unicode(path)

        try:
            return path.decode(self._fsencoding(), 'ignore')
        except (UnicodeError, LookupError):
            return path.decode('utf8', 'ignore')

    def _fsencoding(self):
        """Get the system's filesystem encoding. On Windows, this is always
        UTF-8 (not MBCS).
        """
        encoding = sys.getfilesystemencoding() or sys.getdefaultencoding()
        if encoding == 'mbcs':
            # On Windows, a broken encoding known to Python as "MBCS" is
            # used for the filesystem. However, we only use the Unicode API
            # for Windows paths, so the encoding is actually immaterial so
            # we can avoid dealing with this nastiness. We arbitrarily
            # choose UTF-8.
            encoding = 'utf8'
        return encoding

    def colordiff(self, a, b, highlight='red'):
        """Colorize differences between two values if color is enabled.
    (Like _colordiff but conditional.)
    """
        if self.gv.settings.get_setting('color', self) == 'True':
            return self._colordiff(a, b, highlight)
        else:
            return unicode(a), unicode(b)

    def print_(self, *strings):
        """Like print, but rather than raising an error when a character
        is not in the terminal's encoding's character set, just silently
        replaces it.
        """
        if strings:
            if isinstance(strings[0], unicode):
                txt = u' '.join(strings)
            else:
                txt = ' '.join(strings)
        else:
            txt = u''
        if isinstance(txt, unicode):
            txt = txt.encode(self._encoding(), 'replace')
        print(txt)

    def color_diff_suffix(self, a, b, highlight='red'):
        """Colorize the differing suffix between two strings."""
        a, b = unicode(a), unicode(b)
        if not self.gv.settings.get_setting('color', self) == 'True':
            return a, b

        # Fast path.
        if a == b:
            return a, b

        # Find the longest common prefix.
        first_diff = None
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                first_diff = i
                break
        else:
            first_diff = min(len(a), len(b))

        # Colorize from the first difference on.
        return a[:first_diff] + self.colorize(highlight, a[first_diff:]), \
            b[:first_diff] + self.colorize(highlight, b[first_diff:])

    def choose_candidate(self, candidates, manipulate, opts, item=None, itemcount=None):
        self.print_(u'Candidates:')

        for i, match in enumerate(candidates):
                # Index, metadata, and distance.
            line = [
                u'{0}.'.format(i + 1),
                u'{0}'.format(manipulate.get_stripped_text(match.reference_to_link)
                              )
            ]

            self.print_(' '.join(line))

        # Ask the user for a choice.
        sel = self.input_options(opts, numrange=(1, len(candidates)))

        return sel
