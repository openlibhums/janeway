![CaSSiuS](cassius/images/logo.png?raw=true)
CaSSius is a tool to create beautiful paginated PDF documents from HTML content using CSS regions. It is intended to be part of [XML-first/XML-in workflows](https://www.martineve.com/2015/07/20/building-a-real-xml-first-workflow-for-scholarly-typesetting/) for scholarly communications but may have alternative uses.

CaSSius: heavyweight typesetting with lightweight technology.

#Usage and Quick Start Guide
CaSSius takes standard HTML content in a pre-specified form and flows it between CSS regions (see "document structure" below). To begin using CaSSius follow these steps:

1. Move or copy the "cassius" directory from this repository into the root of your website.
2. Insert the following code into the head tag of your HTML document:

        <link rel="stylesheet" href="cassius/cassius.css">
        <link rel="stylesheet" href="cassius/cassius-content.css">
        <script type="text/javascript" src="cassius/jquery.js"></script>
        <script type="text/javascript" src="cassius/cassius.js"></script>
        <script src="cassius/regions/css-regions-polyfill.js"></script>

3. Optionally, insert the javascript code for [Adobe typekit](https://typekit.com) (you will need to sign up for an account).
4. Format your document according to the "document structure" guide below.
5. Replace cassius/images/logo.png with your own logo.
6. Load the page in a browser, wait until it has finished typesetting and then use the browser's "print to PDF" option to create your document.

#Document Structure
The following rules should be strictly adhered to in order to produce correct documents.

Every HTML file should contain a CaSSius metadata block. A CaSSius metadata block should be wrapped inside a script tag with type set to "text/cassius" and an id attribute of "cassius-metadata. A CaSSius metadata block may contain the following elements:

        <script type="text/cassius" id="cassius-metadata">
            <div id="cassius-metadata-block">
                <div id="cassius-title">Article typeset by CaSSius: heavyweight typesetting with lightweight technology</div>
                <div id="cassius-publication">CaSSius</div>
                <div id="cassius-authors">Martin Paul Eve</div>
                <div id="cassius-affiliations">Department of English and Humanities, School of Arts, Birkbeck, University of London, United Kingdom</div>
                <div id="cassius-emails">martin@martineve.com</div>
                <div id="cassius-doi">10.16995/olh.001</div>
                <div id="cassius-date">September 2015</div>
                <div id="cassius-volume">1</div>
                <div id="cassius-issue">2</div>
            </div>
        </script>

If the "cassius-title" metadata div is not present, CaSSius will use the HTML document's "title" element in the "head" of the document.

The basic structure of a CaSSius document is as follows (also available in [template.html](template.html)):

    <body>
        <div id="cassius-content">
          <h1 class="articletitle"></h1>
          <div class="authors"></div>
          <div class="affiliations"></div>
          <div class="emails"></div>

          <div class="abstract">
              <h2>Abstract</h2>
              <p>Your abstract content here.</p>
              <p>As many paragraphs as needed.</p>
              <p class="oa-info">&copy; 2015 Martin Paul Eve. This is an open-access article distributed under the terms of the Creative Commons Attribution License, which permits unrestricted use, distribution, and reproduction in any medium, provided the original author and source are credited.</p>
          </div>

          <div class="main">
              <div class="section">
                  <h1>A section title</h1>
                  <p>A paragraph.</p>
              </div>

              <div class="section">
                  <h1>A section title</h1>
                  <p>A paragraph with a footnote.<a href="#fn1--fragment" id="xr1"><sup>1</sup></a></p>
              </div>

              <div class="notes">
                  <h1>Notes</h1>
                  <div class="footnote"><p><span class="generated"><a href="#xr1--fragment" id="fn1">1</a></span> Footnote content goes here.</p></div>
              </div>

              <div class="references">
                  <h1 class="ref-title">References</h1>
                  <div class="section ref-list">
                      <ul>
                          <li class="ref-content">Adorno, Theodor W., <i>Negative Dialectics</i>, trans. by E.B. Ashton (London: Routledge, 1973)</li>
                      </ul>
                  </div>
              </div>
          </div>
        </div>

        <article id="article"></article>

        <script type="text/cassius" id="cassius-metadata">
            <div id="cassius-metadata-block">
                <div id="cassius-title">Article typeset by CaSSius: heavyweight typesetting with lightweight technology</div>
                <div id="cassius-publication">CaSSius</div>
                <div id="cassius-authors">Martin Paul Eve</div>
                <div id="cassius-affiliations">Department of English and Humanities, School of Arts, Birkbeck, University of London, United Kingdom</div>
                <div id="cassius-emails">martin@martineve.com</div>
                <div id="cassius-doi">10.16995/olh.001</div>
                <div id="cassius-date">September 2015</div>
                <div id="cassius-volume">1</div>
                <div id="cassius-issue">2</div>
            </div>
        </script>
    </body>

#Import from JATS/NLM
An early-stage version of an import function from JATS is implemented in [cassius-import/bin/cassius-import.py](cassius-import/bin/cassius-import.py). This script requires python and java.

    Usage:
        cassius-import.py <in-file> <out-file> [options]
        cassius-import.py (-h | --help)
        cassius-import.py --version

A sample XML file to show this working (and the scope of implementation to date) [can be found in the cassius-import directory](cassius-import/sample.xml).

#Headless Printing
CaSSius is designed to allow headless printing of documents using wkhtmltopdf, hence the modified version of the CSS Regions Polyfill that we here distribute. Please note that this will not work with the default polyfill and you must use our altered version, although we will attempt to contribute the fix upstream.

The settings that you need to pass to wkhtmltopdf are, for example, as follows:

    ./wkhtmltopdf --javascript-delay 15000 --no-stop-slow-scripts -L 0 -R 0 -B 0 -T 0 http://localhost:8000/ ~/result.pdf

This tells wkhtmltopdf to allow 15 seconds for the polyfill to run, not to stop a script running for a long time and sets all margins to zero. It prints the contents of localhost:8000 to result.pdf in a user's home folder.

#Performance and Settings
If you are consistently typesetting documents that are over fifty pages long, you may see a performance increase if you change the value of initialPages to a higher setting in [cassius.js](cassius/cassius.js). Setting this to a higher value will yield better performance on larger documents, but worse performance on smaller documents.

#Components and Licensing
CaSSius is copyright Martin Paul Eve 2015. It is released under the terms specified in [LICENSE](LICENSE).

CaSSius makes use of several other open-source/free-software projects, including:

* [css-regions-polyfill](https://github.com/FremyCompany/css-regions-polyfill). Copyright (c) 2014 François REMY with [a BSD-style license](https://github.com/FremyCompany/css-regions-polyfill/blob/master/LICENSE.md).
* [jQuery](https://jquery.org). Under [the MIT license](https://jquery.org/license/).
* [docopt](https://github.com/docopt). Copyright (c) 2012 Vladimir Keleshev, <vladimir@keleshev.com> with an [MIT license](https://github.com/docopt/docopt/blob/master/LICENSE-MIT).
* The CaSSius logo is a derivative of a work by [Lil Squid from the Noun Project](https://thenounproject.com/search/?q=type&i=150037), licensed under the Creative Commons Attribution License.
* Parts of the cassius-import library contain materials from the National Library of Medicine, specifically [adaptations of their XSLT suite and entity resolution files, which are public domain](http://dtd.nlm.nih.gov/tools/tools.html).
* The cassius-import library links to the Saxon XSLT and XQuery Processor from Saxonica Limited <http://www.saxonica.com/> which is dual-licensed under the GNU GPL and the Mozilla Public License <http://www.mozilla.org/MPL/>. This dual-licensing applies ONLY to the file saxon9.jar.
