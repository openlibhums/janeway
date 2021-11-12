# Janeway documentation
Python Sphinx project for building the Janeway documentation

## How to build the documentation

### Installing the dependencies
After installing the dependencies for Janeway, install the requirements described under `requirements.txt`
`pip install -r requirements.txt`

### Editing the documentation:
The documentation is written in [reStructuredText](https://docutils.sourceforge.io/rst.html) (rst). Edits can be made to any page under the `docs/source` directory.
When adding a new section to the documentation, it should be added to the navigation under `docs/index.rst`


### Building the documentation
The following options are available from the Makefile:
```
Please use `make target' where target is one of
  html        to make standalone HTML files
  dirhtml     to make HTML files named index.html in directories
  singlehtml  to make a single large HTML file
  pickle      to make pickle files
  json        to make JSON files
  htmlhelp    to make HTML files and an HTML help project
  qthelp      to make HTML files and a qthelp project
  devhelp     to make HTML files and a Devhelp project
  epub        to make an epub
  latex       to make LaTeX files, you can set PAPER=a4 or PAPER=letter
  latexpdf    to make LaTeX and PDF files (default pdflatex)
  latexpdfja  to make LaTeX files and run them through platex/dvipdfmx
  text        to make text files
  man         to make manual pages
  texinfo     to make Texinfo files
  info        to make Texinfo files and run them through makeinfo
  gettext     to make PO message catalogs
  changes     to make an overview of all changed/added/deprecated items
  xml         to make Docutils-native XML files
  pseudoxml   to make pseudoxml-XML files for display purposes
  linkcheck   to check all external links for integrity
  doctest     to run all doctests embedded in the documentation (if enabled)
  coverage    to run coverage check of the documentation (if enabled)
```
The documentation will be built under `docs/build`
When building the HTML documentation via `make HTML`, point your browser to the index page and then you can navigate from there.
e.g `firefox build/html/index.html`

Any changes made to the documentation files will be built as HTML and hosted at https://janeway.readthedocs.io


### Building the documentation with docker
running `make docker` will provision a docker image with all the requirements installed, spin up a container and give you a running shell where the make targets can be run
e.g building the documentation with docker:
```
$ make docker
root@c40d3cadf7ca:/docs# make html
``
