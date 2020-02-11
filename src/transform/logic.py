__copyright__ = "Copyright 2017 Birkbeck, University of London"
__author__ = "Martin Paul Eve & Andy Byers"
__license__ = "AGPL v3"
__maintainer__ = "Birkbeck Centre for Technology and Publishing"
import os
import shutil
import subprocess
import uuid

import pdfkit

from core import files


class CassiusDriver:
    """ A class to control the typesetting tool CaSSius and its JATS importer for automated XML typesetting
    """

    def __init__(self, accessible_temporary_directory, galley, request):
        """ Creates a new CassiusDriver

        :param accessible_temporary_directory: a temporary directory to which the application has write permissions
        :param galley: a galley associated with an article and file
        :param request: the current request object
        """
        from transform import urls
        self.galley = galley
        self.accessible_temporary_directory = accessible_temporary_directory
        self.article_object = galley.article
        self.file_object = galley.file
        self.current_path = os.path.dirname(urls.__file__)
        self.request = request
        self.rewritten_figures = {}

    def transform(self):
        """ Transforms a JATS XML document into a PDF and affiliate it with the current article as a galley

        :return: None
        """
        html, uuid_directory_name, uuid_file_name = self.import_from_jats()
        if html:
            self.replace_logo(uuid_directory_name)
            self.replace_figures(uuid_directory_name, html)
            pdf = self.print_to_pdf(html, uuid_directory_name, uuid_file_name)
            self._store_file(pdf)

        self._cleanup(uuid_directory_name)

    def import_from_jats(self):
        """ Import a JATS file into CaSSius HTML

        :return: a 3-tuple of output_file_path, uuid_directory_name, uuid_file_name
        """
        if not self._check_file_is_xml():
            return None, None, None

        uuid_directory_name, uuid_file_name = self._copy_files_to_accessible_temporary_directory()
        return self._transform_using_xsl(uuid_directory_name, uuid_file_name)

    def replace_logo(self, uuid_directory_name):
        """ Replaces the CaSSius logo with the press logo

        :param uuid_directory_name: the temporary directory on which we are working
        :return: None
        """
        javascript_path = os.path.join(uuid_directory_name, 'cassius', 'cassius.js')
        old_logo_text = "cassius/images/logo.png"

        with open(javascript_path, 'r', encoding="utf-8") as javascript:
            in_data = javascript.read()

        out_data = in_data.replace(old_logo_text, self.request.press.press_cover(self.request))

        with open(javascript_path, 'w', encoding="utf-8") as new_javascript:
            new_javascript.write(out_data)

    def replace_figures(self, uuid_directory_name, html):
        """ Replace the file names of figures with the copied UUID versions. This will handle figures/file.jpg for
        example or file.jpg so long as there is a file affiliated with the article that has an original file name of
        file.jpg.

        :param uuid_directory_name: the temporary directory on which we are working
        :param html: the path to the CaSSius HTML
        :return:
        """
        with open(html, 'r', encoding="utf-8") as html_file_object:
            in_data = html_file_object.read()

        for key, val in self.rewritten_figures.items():
            in_data = in_data.replace('figures/{0}'.format(key), os.path.join(uuid_directory_name, val))
            in_data = in_data.replace('{0}'.format(key), os.path.join(uuid_directory_name, val))

        with open(html, 'w', encoding="utf-8") as new_html:
            new_html.write(in_data)

    def print_to_pdf(self, html_file, uuid_directory_name, uuid_file_name):
        """ Call pdfkit to create a PDF.

        :param html_file: the path to the HTML
        :param uuid_directory_name: the temporary directory on which we are working
        :param uuid_file_name: the unique file name of the original XML
        :return: an output file path of the PDF
        """
        return self._call_pdfkit(html_file, uuid_directory_name, uuid_file_name)

    def _check_file_is_xml(self):
        """ Checks for an acceptable XML input MIME type.

        :return: True if XML, False otherwise
        """
        return self.file_object.mime_type == 'application/xml'

    def _copy_files_to_accessible_temporary_directory(self):
        """ Copies the XML, all images, and CaSSius templates to a temporary UUID directory

        :return: a 2-tuple of uuid_directory_name, uuid_file_name
        """
        uuid_directory_name = os.path.join(self.accessible_temporary_directory, str(uuid.uuid4()))
        uuid_file_name = str(uuid.uuid4())

        # create the sub-folders as necessary
        if not os.path.exists(uuid_directory_name):
            os.makedirs(uuid_directory_name, 0o777)

        # copy the XML file
        shutil.copy(self.file_object.get_file_path(self.article_object),
                    os.path.join(uuid_directory_name, uuid_file_name))

        # copy the CaSSius files
        shutil.copytree(os.path.join(self.current_path, "cassius", "CaSSius", "cassius"),
                        os.path.join(uuid_directory_name, "cassius"))

        # copy all data and figure files
        for data_file_object in self.article_object.data_figure_files.all():
            new_data_file_name = str(uuid.uuid4())

            shutil.copy(data_file_object.get_file_path(self.article_object),
                        os.path.join(uuid_directory_name, new_data_file_name))

            # store the old file name as a key and the new file name as a value in this dictionary
            self.rewritten_figures[data_file_object.original_filename] = new_data_file_name

        for image in self.galley.images.all():
            new_image_file_name = str(uuid.uuid4())

            shutil.copy(image.get_file_path(self.article_object),
                        os.path.join(uuid_directory_name, new_image_file_name))

            # store the old file name as a key and the new file name as a value in this dictionary
            self.rewritten_figures[image.original_filename] = new_image_file_name

        return uuid_directory_name, uuid_file_name

    def _transform_using_xsl(self, uuid_directory_name, uuid_file_name):
        """ Transforms a document from XML to HTML

        :param uuid_directory_name: the temporary directory on which we are working
        :param uuid_file_name: the temporary file name of the XML
        :return: a 3-tuple of output_file_path, uuid_directory_name, uuid_file_name
        """
        xslt_path = os.path.join(self.current_path, 'cassius', 'cassius-import', 'bin')
        xml_path = os.path.join(uuid_directory_name, uuid_file_name)
        output_file_path = '{0}.html'.format(xml_path)

        command = "java -cp '{0}{1}saxon9.jar':'{0}{1}..{1}runtime{1}xml-resolver-1.1.jar':'{0}{1}..{1}runtime{1}' net.sf.saxon.Transform -r:org.apache.xml.resolver.tools.CatalogResolver -y:org.apache.xml.resolver.tools.ResolvingXMLReader -x:org.apache.xml.resolver.tools.ResolvingXMLReader -u -o '{2}' '{3}' '{0}{1}..{1}transform{1}xsl{1}cassius-main.xsl'".format(
            xslt_path, os.sep, output_file_path, xml_path)

        subprocess.call(command, stdin=None, shell=True)

        return output_file_path, uuid_directory_name, uuid_file_name

    def _call_pdfkit(self, html_file, uuid_directory_name, uuid_file_name):
        """ Runs wkhtmltopdf to create a PDF file.

        :param html_file: the input HTML
        :param uuid_directory_name: the temporary directory on which we are working
        :param uuid_file_name: the XML UUID file name from which the HTML was derived
        :return: the output file path
        """
        pdfkit_options = {
            'margin-top': '0',
            'margin-right': '0',
            'margin-bottom': '0',
            'margin-left': '0',
            'encoding': 'UTF-8',
            'javascript-delay': '9000',
            'no-stop-slow-scripts': '',
        }

        pdfkit_config = pdfkit.configuration(
            wkhtmltopdf=bytes(os.path.join(self.current_path, 'cassius/' 'bin', 'wkhtmltopdf'), 'utf-8')
        )

        pdfkit_output_file = '{0}.pdf'.format(os.path.join(uuid_directory_name, uuid_file_name))

        pdfkit.from_file(html_file, pdfkit_output_file, options=pdfkit_options, configuration=pdfkit_config)

        return pdfkit_output_file

    def _store_file(self, file_path):
        """ Affiliates a file with an article

        :param file_path: the file path
        :return: None
        """
        from core import models as core_models
        new_file = files.copy_local_file_to_article(file_path, 'article.pdf', self.article_object,
                                                    self.request.user, label="PDF", galley=True)
        self.article_object.manuscript_files.add(new_file)

        core_models.Galley.objects.create(
            article=self.article_object,
            file=new_file,
            label='PDF',
            type='pdf',
            sequence=self.article_object.get_next_galley_sequence()
        )

    @staticmethod
    def _cleanup(uuid_directory_name):
        """ Deletes a temporary directory

        :param uuid_directory_name: the temporary directory to delete
        :return: None
        """
        shutil.rmtree(uuid_directory_name)
