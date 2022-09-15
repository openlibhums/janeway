Identifiers
===========

Support for minting Digital Object Identifiers (DOIs) with Crossref is built into Janeway's core. We will be expanding this to other providers in the future.

When Are DOIs Minted?
---------------------
If all the settings are properly configured (see below), Janeway handles DOI registration for you, stepping in at a few key points in the publishing pipeline.

By default, a DOI is registered (a.k.a. minted, deposited) with Crossref when an article is accepted for publication. Some provisional metadata is sent at this time (No author-identifiable details are shared).
When an article is scheduled for publication, a new request is sent to Crossref to update all metadata records.

.. tip::
    You can let editors see a preview of the data that gets sent before accepting an article. See **Accept Article Warning** under :ref:`Review Settings<reviewsettings>`.

At this stage, the DOI will be registered with Crossref, but the webpage it points to on your journal website may not be active yet if the article isn't published yet. That's normal.

The DOI is deposited with Crossref again when the article is published, so any metadata updated in the interim will also be updated in Crossref's metadata feeds. This is also when the DOI starts working as a permalink, in addition to being a unique identifier.

There are things that might interrupt this default behavior. If you are importing backlist content, or there's an issue with the Crossref settings entered, or the required metadata isn't there, you may need to take a more active role. That's where the DOI Manager comes in.

.. _doimanager:

DOI Manager
-----------
You can see all the DOIs for a journal (if you are an editor) or for a press (if you are a staff member) in the DOI Manager.

First, filter by date, registration status, or primary issue until you have an actionable set of articles.

At the moment, the DOI Manager can handle small batches, such as 20 articles, with no problems, but it may not be able to handle larger batches very well. We will optimize it to handle large batches in the future.

In some cases, you can preview the XML that will get sent to Crossref.

Once you have filtered the articles to your liking, you can take two actions: **Register DOIs** and **Poll for status**. **Register DOIs** will package up all the metadata into XML and send it to Crossref. Crossref will put all the deposits they receive in a queue to process, so the status may not be immediate. After a few moments (or longer if it is a large batch), you can use **Poll for status** to check the result.

.. warning::
    **Poll for status** on a large group of articles could take a long time, so test it out on a smaller group first.

.. _interpreting-registration-status:

Interpreting Registration Status
--------------------------------

Unknown
    Janeway doesn't know the status. Try **Poll for status**.

Not yet registered
    This DOI hasn't been registered yet. You can register it if what you see in the **DOI** column looks right (including pattern previews).

Queued at Crossref
    The deposit batch you sent is waiting to be read by the Crossref servers.

Registered
    Success! Crossref understood all the metadata you sent and didn't find any problems with it. 

.. tip::
    A status of **Registered** does not necessarily mean that the DOI will resolve correctly, if the URL it points to isn't fully operational yet on the Janeway side (i.e., the article isn't published).

Registered (but some citations not correctly parsed)
    Crossref understood the article-level metadata, but when it went to process the citations, there were errors. Check the XML in the **Response** column for details.

Registered with warning
    Crossref understood and registered the DOI, but sent back a warning. Check the XML in the **Response** column for details.

Registration failed
    Crossref tried to register the DOI but couldn't because of a problem. Check the XML in the **Response** column for details.

Crossref Settings
-----------------
To edit the Crossref settings, select **Crossref Settings** from the manager interface. The fields are as follows:

Use Crossref DOIs
    If disabled, no DOIs will be minted

Use Crossref Test Deposit Server
    If enabled, DOIs will be minted on Crossref's test system

Crossref Username
    Your crossref username

Crossref Password
    Your crossref password

Crossref Depositor Email
    The email address of the depositor

Crossref Depositor Name
    The name of the depositor

Crossref Prefix
    The prefix for your crossref account -- usually 10.XXXX

Crossref Registrant Name
    The name of the registrant for this journal on Crossref's system (e.g. Open Library of Humanities)

DOI Display Prefix
    Text to prepend to DOIs -- used to generate DOI URLs

DOI Display Suffix
    Text to append to DOIs -- also used to generate DOI URLs

DOI Pattern
    The pattern for auto-generating DOIs. Defaults to using the journal code and article ID (e.g. ``orbit.123``):

        ``{{ article.journal.code }}.{{ article.pk }}``

Title DOI
    The DOI (not in URL format) registered for this journal (e.g. ``10.001/my-journal``). It is included on all deposits for this journal. It must be registered ahead of time.

    It is mandatory for a journal to have a DOI registered **only** when an ISSN is not available for a journal, as Crossref requires at least one unique identifier for every journal.

    However, even if your journal has an ISSN, Crossref still recommends registering a DOI for your journal. We recommend using your journal code as the DOI. For example, with the prefix of ``10.0001`` and the journal code of ``abcd``, you could set the journal DOI to ``10.0001/abcd``.

Issue DOI Pattern
    Janeway supports minting DOIs for journal issues automatically. With this setting, you can define the pattern used to generate the issue-level DOI that will be used for registration.

    With the default pattern, an issue with ID ``1`` (and prefix ``10.0001``, and journal code ``abcd``) will have a generated DOI of ``10.0001/abcd.issue.1``.

    A collection with an ID of ``2`` would have a generated DOI of ``10.0001/abcd.collection.2``.

Auto-register issue-level DOIs
    When enabled, issues will have a DOI assigned and registered as soon as the first article in the issue is scheduled for publication. If an issue DOI has not been entered manually, Janeway will use the pattern defined in the setting above to generate one automatically.


Crosscheck Settings
-------------------
Janeway also has support for Crosscheck (also called Similarity Check), which is provided by iThenticate. You can sign up for an account via Crossref and this will allow you to send submitted manuscripts for originality checking.

The settings are:

Enable
    Enables display for Crosscheck buttons

Username
    Your iThenticate service username

Password
    Your iThenticate service password

More info on Crosscheck/Similarity Check: https://www.crossref.org/services/similarity-check/
