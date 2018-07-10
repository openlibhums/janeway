#!/usr/bin/env python
# Imports basic JATS XML documents into CaSSius-compatible HTML document formats
# Copyright Martin Paul Eve 2015

"""cassius-import: Imports a JATS XML document into a CaSSius-compatible HTML document

Usage:
    cassius-import.py <in-file> <out-file> [options]
    cassius-import.py (-h | --help)
    cassius-import.py --version

Options:
    -d, --debug                                     Enable debug output.
    -h --help                                       Show this screen.
    --version                                       Show version.
"""


import os
from os import listdir
from os.path import isfile, join
import re
from debug import Debug, Debuggable
from docopt import docopt
from interactive import Interactive
import subprocess


class CassiusImport (Debuggable):
    def __init__(self):
        # read  command line arguments
        self.args = self.read_command_line()

        # absolute first priority is to initialize debugger so that anything triggered here can be logged
        self.debug = Debug()

        Debuggable.__init__(self, 'cassius-import')

        self.in_file = self.args['<in-file>']
        self.out_file = self.args['<out-file>']

        self.dir = os.path.dirname(os.path.abspath(__file__))

        if self.args['--debug']:
            self.debug.enable_debug()

        self.debug.enable_prompt(Interactive(self.args['--debug']))

    @staticmethod
    def read_command_line():
        return docopt(__doc__, version='cassius-import v0.1')

    def run(self):
        command = "java -cp '{0}{1}saxon9.jar':'{0}{1}..{1}runtime{1}xml-resolver-1.1.jar':'{0}{1}..{1}runtime{1}' net.sf.saxon.Transform -r:org.apache.xml.resolver.tools.CatalogResolver -y:org.apache.xml.resolver.tools.ResolvingXMLReader -x:org.apache.xml.resolver.tools.ResolvingXMLReader -u -o '{2}' '{3}' '{0}{1}..{1}transform{1}xsl{1}cassius-main.xsl'".format(self.dir, os.sep, self.out_file, self.in_file)
        #command = "java -jar '{0}{1}saxon9.jar';'{0}{1}..{1}runtime{1}xml-resolver-1.1.jar' -o '{2}' '{3}' '{0}{1}..{1}transform{1}xsl{1}cassius-main.xsl'".format(self.dir, os.sep, self.out_file, self.in_file)

        # -r org.apache.xml.resolver.tools.CatalogResolver -catalog '{0}{1}..{1}runtime{1}catalog.xml'

        self.debug.print_debug(self, u'Running saxon transform (JATS -> CaSSius)')

        subprocess.call(command, stdin=None, shell=True)


def main():
    cwf_instance = CassiusImport()
    cwf_instance.run()


if __name__ == '__main__':
    main()
