from django.test import TestCase

from production.logic import remove_css_from_html

class TestLogic(TestCase):

    def test_remove_css_from_html(self):
        test_html = """
            <html>
              <head>
                <link rel="stylesheet" type="text/css" href="mystyle.css">
              </head>
              <body>
                <style>
                  .banana{"width": 100}
                </style>
                <p style="color:red;">This is a paragraph.</p>
              </body>
            </html>
        """
        expected_html = '<html>\n <head>\n </head>\n <body>\n  <p>\n   This is a paragraph.\n  </p>\n </body>\n</html>\n'

        result = remove_css_from_html(test_html)
        self.assertMultiLineEqual(result, expected_html)

