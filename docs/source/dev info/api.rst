API
===

API stands for Application programming interface. APIs are designed to allow two or more programs to interact with one another.

OAI-PMH
-------
Janeway currently supports Dublin Core (the default) and JATS metadata prefixes. Janeway implements OAI-PMH feeds at three site levels:

- Press
    - This top level OAI-PMH feed will include records for all journal articles in the Janeway installation.
- Journal
    - The journal OAI-PMH feed contains only records for articles in this journal.
- Repository
    - The repository feed contains only records for objects in this repository.

Currently there is no central list of OAI-PMH URLs but they can be extrapolated.

If your installation uses individual domains for each site then the endpoint can be worked out as follows:

https://yoursitedomain.com/api/oai/

A live example of this pattern can be seen on the OLH install of Janeway:

https://olh.openlibhums.org/api/oai/

If your installation uses path mode with a single domain for each site then the endpoint can be worked out as follows:

https://yoursitedomain.com/repe_or_journal_code/api/oai

A live example of this patter can be seen on the UMass Chan Medical install of Janeway:

https://publishing.escholarship.umassmed.edu/jeslib/api/oai/

More information on how OAI-PMH feeds work can be found on the Open Access Initiative site: https://www.openarchives.org/pmh/
