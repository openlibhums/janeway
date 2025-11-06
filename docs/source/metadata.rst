Metadata
========

Author metadata
---------------

Author records include name, email, biography, affiliations, and optional contributor roles, including structured persistent identifiers for people, organizations, and roles. These records are created by authors during the article submission phase, and they remain with the article permanently. Editors can change them throughout the workflow stages as needed.

.. note::
   Technically, editors can also change author records after publication, to handle important name changes when requested. But it is best to avoid edits after publication if possible, and it may not always be possible to change the name everywhere it appears, in search results, discovery services, and typeset versions of the article.

Records for authors are distinct from user accounts. So if you choose to delete your user account after you publish an article, or if your affiliations change, your author record remains intact, to maintain a public record of your authorship at the time of publication.

If you are a correspondence author, you must have a user account linked to your author record. But if another author is handling the correspondence, you do not need to have an account.

Janeway remembers the order of author records, as set by the submitting author. Editors can change it later too if needed. This order is used to set the sequence of author names wherever they are output in metadata or displayed to readers.

.. tip::
    For ease of use and better metadata, authors with ORCID accounts are encouraged to use the ORCID login option, and author records should be added by searching the ORCID registry, rather than manual entry.

Metadata standards
------------------

Janeway integrates with a number of common open metadata standards to support interoperability, discovery, and data management.

Research Organization Registry (ROR)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To assess the reach of publishing activities, it can be valuable to group publications by the research organizations that stand behind them. However, problems arise when people describe their affiliations in slightly different ways, when organizations have names in more than one language, or when two organizations have the same name.

These problems are solved by the `Research Organization Registry <https://ror.org/>`_. They assign persistent identifiers to organizations, like DOIs for articles, ORCIDs for people, and ISBNs for books. This allows multiple names to be associated with a single organization, for easier discovery and display, and it adds to the possibilities for linked open data. The ROR team regularly updates and maintains the registry, which in 2025 included more than 114,000 entries from around the world.

Janeway integrates with ROR from the point of submission through to publication and metadata distribution. When authors first submit a manuscript to a Janeway journal, they are asked to search in registry data for their affiliated institutions. And if they signed in via ORCID, Janeway pulls over their primary affiliation from their public ORCID profile, usually with ROR IDs in tow. Other users such as editors can also create affiliations that are connected to ROR data.

When Janeway metadata is distributed, the persistent identifier is provided alongside the organization names. This way, other platforms and discovery services can understand Janeway affiliation metadata unambiguously and programmatically, without the need for intensive data curation, cleaning, or matching.

ROR data is available from Janeway in these places:
  - journal article web pages (HTML)
  - auto-generated JATS XML stubs
  - Crossref deposits (XML)
  - the OAI-PMH feed (XML)
  - the Open Access Switchboard (via the **OA Switchboard** plugin)

ROR data can be integrated in these places in the future:
  - the repository system
  - reports (via the **Reporting** plugin)
  - metadata imports and exports (via the **Imports** plugin)
  - Datacite deposits (via the **Datacite** plugin)
  - the **Supporters** plugin

Typesetters have access to ROR data and are encouraged to encode it in any JATS XML they produce for Janeway.

Contributor Role Taxonomy (CRediT)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

What does an author do? What do coauthors do? Many things, and not always the same ones. How do you represent this in metadata?

The `CRediT system <https://credit.niso.org/>`_ standardizes fourteen roles that are common in collaborative research and authorship, with names like "Conceptualization" and "Writing - original draft." If a journal chooses to turn this system on, each contributor's effort can be described with one or more of these terms.

Each CRediT term is connected to a persistent identifier with a URI form, so CRediT data can be used in linked data environments alongside ORCIDs and ROR IDs.

CRediT data is distributed by Janeway in these places:
  - on journal article web pages (HTML)
  - in auto-generated JATS XML stubs
  - the OAI-PMH feed (XML)
  - the Open Access Switchboard (via the **OA Switchboard** plugin)

CRediT data can be integrated in these places in the future:
  - in Crossref deposits (XML)
  - metadata imports and exports (via the **Imports** plugin)
  - the repository system
  - Datacite deposits (via the **Datacite** plugin)

Typesetters have access to CRediT data and are encouraged to encode it in any JATS XML they produce for Janeway.
