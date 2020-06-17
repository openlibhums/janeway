Typesetter Guide
================
When a typesetting task is assigned you will receive an email notification and also be able to see the task on your dashboard under _Production_.

.. figure:: nstatic/production_block.png

    Production block

Clicking on view requests will display three columns

- Awaiting Decision
    - New Assignments.
- In Progress
    - Assignments you have accepted but no completed.
- Completed
    - Assignments you have completed.

.. figure:: nstatic/typesetting_requests.png

    Typesetting requests

Typesetting a Paper
-------------------
Once you have accepted a request you can then use the view button to display the typesetter interface. This allows typesetters to pull files and view the metadata of the paper so they can produce Galley proofs. The interface is broken in 4 sections.

- Files uploaded for production
    - Lists the files that are to be used in generating the galley proofs.
- Current Galleys
    - Lists any galley proofs that already exist.
- Source Files
    - This is an area for you to upload any intermediate source files (indesign etc).
- Notes
    - Displays the request from the editor and a link to view the article's metadata.

.. figure:: nstatic/typeset_article.png

    Typesetter interface

Uploading a Galley
------------------
You can use the Upload a new galley button to upload a new file. There are three upload options.

- XML/HTML
- PDF
- Other (for any other file types)

Janeway processes each differently (or in the case of Other, not at all) so ensure you select the correct upload box.

.. warning::
    Janeway operates with the UTF8 encoding, so you should ensure your plain text galleys (HTML and XML) use this encoding.

Missing Supplements
^^^^^^^^^^^^^^^^^^^
When you upload an XML or HTML galley Janeway will scan it for images and warn you if there you need to upload those images. You can do this by editing the galley file.

.. figure:: nstatic/galleys.png

    Article with galleys, XML galley has two missing images

In the Edit Galley screen you can upload individual image files, select from exising figure files or upload a zip file of images.

.. tip::
    If you have lots of images ensure they have the correct name (eg, whatever they are called in the XML/HTML file) and zip them. You can use the zip uploaded to upload them in one go.

Managing Galleys
----------------
In addition to uploading images alongside galley files you can also:

- Replace the galley if you've made changes to the original file.
- Upload a CSS file to go along with the galley.
- Change the XSLT file used to render the galley.
- View the galley's history or delete it.

Completing Typesetting
----------------------
Once you have uploaded the required galleys and their files you will notice a new Note to Editor box has appeared in the Notes section, you can use this to complete your task.

Once you have marked it as complete the card will move into the Completed column.