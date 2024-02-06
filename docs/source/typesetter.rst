Typesetter Guide
================
When you have been assigned a typesetting task, you will receive an email notification containing a link. This link will lead to the Janeway Dashboard.

.. note:: This workflow guide assumes you are using the updated typesetting workflow (also known as the 'typsetting plugin'). If you are not, please contact us as we may need to update your install.

.. figure:: nstatic/Typesetting_dashboardblock.png
    :alt: The typesetter Dashboard displaying the number of typesetter tasks assigned.

    Typesetter dashboard block block

From here, you will be able to see the number of open typesetting assignments you have. If you click on this, it will take you to the ‘Typesettings Assignments’ page. Here you can view your currently open typesetting assignments (the top block) and your completed assignments (the bottom block).

For the open assignments, it will display:
- Title
- Current typesetting round
- Date is was assigned
- Due date
- Time to due date

For the completed assignments, it will display:
- Title
- Typesetting round
- Date it was assigned
- Completion date

.. figure:: nstatic/Typesetting_assignments.png
    :alt: The ‘Typesettings assignments’ page.

You can then click ‘View Assignment’ to display the assignment page.

Typesetting a Paper
-------------------
On this page, you will find relevant information about the typesetting task. This will include the instructions, manuscript files, metadata, options to accept or decline the task, and space to upload completed files.

.. figure:: nstatic/Typesetting_assignments.png
    :alt: The ‘Assignment information’ page.

This page is broken in three sections.

- Assignmentment information
    - In this section, you will be able to see any comments from the editor or proofreaders which have been provided to you. You will also be able to view and download the files to typeset (manuscript files), any supplementary files, and space to upload your completed work and source files (if required).
- Metadata
    - This is where you will find all of the relevant metadata for the typesetting task.
- Complete typesetting
    - Under this section, you can leave any notes you may have to the editors. This is also where you will mark the assignment as complete to submit the uploaded files.

Uploading a Typeset File
^^^^^^^^^^^^^^^^^^^^^^^
You can use the ‘Upload a New Typeset File’ button to upload a new typeset file. 

Source files (such as Adobe In Design files) can be uploaded using the ‘Upload New Source File’ button (if required).

.. figure:: nstatic/typesetting_files.png
    :alt: The files section of the typesetting page. It shows the ‘Files to typeset’, ‘Upload typeset files’ and ‘Upload source file’ options.

.. figure:: nstatic/typesetting_upload.png
    :alt: The ‘Upload a typeset file’ upload. It provides the options to provide a label for the file, toggle whether the file should be publicly available after the article is published, choose a file to upload and then confirm the upload.

Janeway will attempt to provide an appropriate label if this is left blank. If you wish to make sure the label is correct, you can enter a filetype label in this textbox. For instructions on how to edit a label, please see the section below.

.. Warning::
    Janeway operates with the UTF8 encoding. Please ensure that any HTML and XML files you upload use this encoding.


Editing typeset files and uploading additional files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
If you need to make changes to the typeset files and reupload it or upload additional files, this can be done through the ‘Edit Typeset File’ page. This page can be accessed by clicking on the ‘Edit’ button.

.. figure:: nstatic/typesetting_edit_button.png
    :alt: The ‘Upload typeset files’ section, showing two uploaded files. It displays the following metadata for the file: Janeway ID, label, filename and date it was last modified. Additionally, it displays the following options: edit, download and preview. It also displays the figure files’ status: ‘N/A’ for a file with no figure files and ‘Missing figures’ for a file with missing figures.

.. figure:: nstatic/Typesetting_filehistory.png
    :alt: The ‘Edit typeset file’ page.

This page is broken in three sections:
- The typeset file
	- Here you can replace the typeset file, see the file history.
- Typeset file details
	- Here you can edit the file label which denotes the filetype.
- Additional file uploads
    - Select from images existing image files
    - Upload individual image files
    - Upload a zip file of images
    - Upload a CSS file to go along with the galley
    - Change the XSLT file used to render the galley

Managing typeset files
^^^^^^^^^^^^^^^^^^^^^
In the first section of the page, you can view the file currently uploaded, and replace or download it. You can also view the file's history by clicking on the button under 'History'. 

This will open a page where you can download and re-instate previous versions uploaded, or delete the current file entirely (in case you have uploaded an incorrect file).

.. figure:: nstatic/edit_typesetting_file.png
    :alt: The File history and metadata page. It shows the article’s metadata, previous versions of the file (with options to download or re-instate them), and the current version (with the option to download, replace and delete it).

Managing images / figure files
^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. figure:: nstatic/typesetting_image_upload
    :alt: A screenshot displaying the available options for adding image files: uploading a file in a section for a dedicated image (displaying its filename), uploading images as additional files or uploading a zip file.

When a file that has been typeset in HTML or XML contains image links, Janeway will detect these and prompt you to upload the image files.The file names should match the src or href used in the XML/HTML and should be relative (e.g. src="fig1.jpg").

If the image files were already uploaded onto Janeway, you can select them instead.

If you need to upload a large number of images, it might be faster to use the zip uploader (see ‘Upload Zip File’ in the image below). To do so, create a .zip archive file with all of the image files. The image filename must match the link in the typeset file, otherwise it will not import them.

Styling
^^^^^^^
On this page, you can also upload a CSS file associated with the article for an individual style, if required. We recommend avoiding style changes to the header and footer type elements as this will affect the layout of the page.

You can also select the XSL file used for rendering the HTML out of the file. This will be the Janeway default (1.4.3.) except if explicitly instructed otherwise (this will be communicated by the editors as part of the typesetting task or agreement).

Finishing Up
^^^^^^^^^^^^

Once you are done with the typesetting (or correction) task, you can leave a note for the editor and complete it for the editor to review. Please note that once you complete the task, you will be unable to return to this page.

.. note:: If you attempt to complete the typesetting task with potential issues remaining (e.g. missing image files, typeset files that have not been corrected), Janeway will warn you about this.

.. figure:: nstatic/typesetting/images_missing_warning.png
    :alt: A missing figure warning. It reads "Some of the typeset files don't have their images uploaded." Below it the file and filetype are displayed and the following text: "You can add images to the typeset file by hitting 'Edit'. A menu will show you which images are missing."

Typesetting Recipes
-------------------

Right-to-Left Text Direction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. highlight:: xml

Arabic and many other languages are written right to left, requiring special markup in an XHTML environment that operates left-to-right by default.

Here is an example in JATS XML of an isolated bit of Arabic text in a document that is otherwise left-to-right:

.. figure:: nstatic/typesetting/arabic-rtl-jats-xml.png

Make sure you use a text editor that shows zero-width unicode characters, like U-2067. The above screenshot is an XML file opened in VS Code.

Here is the rendered output:

.. figure:: nstatic/typesetting/arabic-rtl-rendered.png

Notice the following about the code sample:

1. On each line, begin with the `RLI unicode character (U+2067) <https://www.unicode.org/reports/tr9/#Explicit_Directional_Isolates>`_ at the beginning of the line to explicitly trigger  right-to-left rendering for the remainder of the line, including symbols like periods that the browser would otherwise render left-to-right. This is roughly equivalent to the HTML attribute `dir="rtl"`. If working with periods or other punctuation, note that they may appear on the right in your code editor, but render on the left in the browser.

2. Wrap each line in the `styled-content JATS element <https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/styled-content.html>`_ and apply a `style attribute <https://jats.nlm.nih.gov/publishing/tag-library/1.3/attribute/style.html>`_ specifying CSS for right text alignment and block display.

3. When working with long lines of text, make sure not to introduce arbitrary line breaks.

Center Alignment
^^^^^^^^^^^^^^^^

.. highlight:: xml

In some cases you might need to center-align text::

    <p>Then came the apotheosis of modernism:</p>
    <disp-quote>
        <styled-content style="text-align: center; display: block;">
            Leaves are falling
        </styled-content>
    </disp-quote>

The output is:

.. figure:: nstatic/typesetting/text-align-center.png

This is accomplished with the the `styled-content JATS element <https://jats.nlm.nih.gov/publishing/tag-library/1.3/element/styled-content.html>`_ and a `style attribute <https://jats.nlm.nih.gov/publishing/tag-library/1.3/attribute/style.html>`_ specifying CSS for center text alignment and block display.
