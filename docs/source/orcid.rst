ORCID Sign In
======================
Janeway has had support for ORCID login for some time. It can be enabled by adding the following to your settings file.

::

    ENABLE_ORCID = True
    ORCID_CLIENT_SECRET = ''
    ORCID_CLIENT_ID = ''

As the URLs for the ORCID API are fixed there is no need to set them.

Callback URLs
-------------
You will need to set the callback URLs in the ORCID interface. If using domain mode you will need to add each domain, if using path you can set just the main domain.