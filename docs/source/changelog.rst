Changelog
=========
v1.3.10
-------
Version 1.3.10 includes updates mainly for Peer Review. Updates to documentation will be released with a later Release Candidate.

Bugfixes
^^^^^^^^
* The Edit Metadata link now shows for Section Editors (https://github.com/BirkbeckCTP/janeway/pull/2183)
* Fixed a bug where the review assignment page wouldn't load if a reviewer had multiple ratings for the same review (https://github.com/BirkbeckCTP/janeway/issues/2168)
* Fixed wrong URL name in review_accept_acknowledgement (https://github.com/BirkbeckCTP/janeway/pull/2165)
* Section editors are now authorised by the `article_stage_accepted_or_later_or_staff_required` security decorator (https://github.com/BirkbeckCTP/janeway/pull/2162)
* The edit review assignment form now works properly after a review has been accepted (https://github.com/BirkbeckCTP/janeway/pull/2156)
* When a revision request has no editor we now fallback to email journal editors rather than sending no email (https://github.com/BirkbeckCTP/janeway/pull/2150)
* Only published issues display in the Issue sidebar (https://github.com/BirkbeckCTP/janeway/issues/2113)
* Empty collections are now excluded from the collections page (https://github.com/BirkbeckCTP/janeway/pull/2139)
* When revising a file the supplied label is retained and defaults now to "Revised Manuscript" (https://github.com/BirkbeckCTP/janeway/issues/2128)
* Guest Editors now display properly on Issue pages (https://github.com/BirkbeckCTP/janeway/issues/2134)
* Fixed potential validation error when sending emails using the contact popup (https://github.com/BirkbeckCTP/janeway/issues/1967)
* Fixed issue where when two or more review form elements had the same name the review would not save (https://github.com/BirkbeckCTP/janeway/pull/2108)


Workflow (Review)
^^^^^^^^^^^^^^^^^
* The draft decisions workflow has been updated to be more user friendly (https://github.com/BirkbeckCTP/janeway/issues/1809)
* Article decisions have been moved from the main review screen to a Decision Helper page (https://github.com/BirkbeckCTP/janeway/issues/1809)
* When using the enrol pop up when assigning a reviewer you can now select a salutation (https://github.com/BirkbeckCTP/janeway/issues/2143)
* The Request Revisions page has had some of its wording updated (https://github.com/BirkbeckCTP/janeway/issues/2131)
* The Articles in Review page has has some of its wording updated and now displays even more useful information (https://github.com/BirkbeckCTP/janeway/issues/2122)
* Review Type has been removed from the Review Assignment form (https://github.com/BirkbeckCTP/janeway/pull/2119)
* The Review Form page now displays useful metadata for the Reviewer (https://github.com/BirkbeckCTP/janeway/issues/2101)
* Added a Email Reviewer link to the Review Detail page (https://github.com/BirkbeckCTP/janeway/issues/1967)
* Added tooltips to user action icons and moved reminder link to dropdown (https://github.com/BirkbeckCTP/janeway/issues/2002)

Emails
^^^^^^
* The Peer Review Request email now contains useful metadata (https://github.com/BirkbeckCTP/janeway/issues/2100)
* `send_reviewer_accepted_or_decline_acknowledgements` now has the correct link and more useful information (https://github.com/BirkbeckCTP/janeway/issues/2102)

Author Dashboard
^^^^^^^^^^^^^^^^
* You can enable the display of additional review metadata for authors. Originally this was always available but is now a toggle-able setting that is off by default (https://github.com/BirkbeckCTP/janeway/issues/2103)

Manager
^^^^^^^
https://github.com/BirkbeckCTP/janeway/issues/2149
* The Users and Roles pages have been updated to:
    * Enrolled Users (those users who already have a role on your journal)
    * Enrol Users (allows you to search, but not browse, users to enrol them on your journal)
    * Roles (now only displays users with the given role)
* One click access is now enabled by default for all new journals (https://github.com/BirkbeckCTP/janeway/pull/2105)


Front End
^^^^^^^^^
* Added support for linguistic glosses (https://github.com/BirkbeckCTP/janeway/issues/2031)
* Privacy Policy links are now more visible on Registration pages (https://github.com/BirkbeckCTP/janeway/pull/2174)

## Crossref & Identifiers
https://github.com/BirkbeckCTP/janeway/issues/2157
* Crossref deposit has been update:
    * Authors are now in the correct order
    * Abstracts are included
    * Date accepted is included
    * Page numbers are included
* Publisher IDs can now have . (dots) in them (https://github.com/BirkbeckCTP/janeway/pull/2173)

## Docker
* When running docker using Postgres a pgadmin container is automatically connected (https://github.com/BirkbeckCTP/janeway/pull/2172)


v1.3.9
------

Workflow
^^^^^^^^

* A new setting has been added to enable a Review Assignment overview to appear on the list of articles in review. This will display the initials of the reviewer, the current status of the review and when it is due and includes colour coding to assist. This can be enabled from the Review Settings page. [Manager > Review Settings] `#1847 <https://github.com/BirkbeckCTP/janeway/pull/1847>`_
* When no projected issue is assigned to an article users are warned that Typesetters will not know which issue the paper will belong to `#1877 <https://github.com/BirkbeckCTP/janeway/issues/1877>`_
* Peer Reviewers can now save their progress `#1868 <https://github.com/BirkbeckCTP/janeway/issues/1868>`_
* Section Editors will now work as expected when assigned to a section to work on (#1934)

Front End
^^^^^^^^^
* A bug on the /news/ page caused by not having a default banner image has been fixed `#1879 <https://github.com/BirkbeckCTP/janeway/issues/1879>`_
* Editors can now exclude the About section from the Submissions page. `#1881 <https://github.com/BirkbeckCTP/janeway/pull/1881>`_

Authentication
^^^^^^^^^^^^^^
* Fix integrity issues when editing a user profile with mixed case email addresses. `#1807 <https://github.com/BirkbeckCTP/janeway/pull/1807>`_

Themes
^^^^^^

* The OLH theme build_assets command now handles Press overrides. `#1821 <https://github.com/BirkbeckCTP/janeway/pull/1821>`_
* The privacy policy link on the footer can now be customized for the press and for the journals via a setting under Journal settings, A default can be set for all journals press 'Journal default settings'.
* Material now has social sharing buttons similar to what OLH theme already provided `#1995 <https://github.com/BirkbeckCTP/janeway/pull/1995>`_

Frozen Authors
^^^^^^^^^^^^^^
* Frozen author metadata was being overridden when calling article.snapshot_authors. There is now a force_update flag to control this behaviour. `#1832 <https://github.com/BirkbeckCTP/janeway/pull/1832>`_
* Refactored the function to iterate the authors in article.snapshot_authors so that authors without an ArticleAuthorOrder record are not ignored. `#1832 <https://github.com/BirkbeckCTP/janeway/pull/1832>`_

Manager/Settings
^^^^^^^^^^^^^^^^

* Staff members can now merge accounts together from the press manager #1857
* Editor users can now access the Review and Revision reminder interface. [Manager > Scheduled Reminders] `#1848 <https://github.com/BirkbeckCTP/janeway/pull/1848>`_
* Editors can now soft delete review forms. When deleted thay are hidden from the interface. Admins and Superusers can reinstate them from Admin. `#1854 <https://github.com/BirkbeckCTP/janeway/pull/1854>`_
* Editors can now drag-and-drop reorder review form elements, elements are now ordered automatically. `#1853 <https://github.com/BirkbeckCTP/janeway/pull/1853>`_
* Fixed a bug that would override the default setting. `#1861 <https://github.com/BirkbeckCTP/janeway/issues/1861>`_

APIs
^^^^
* Janeway's OAI implementation now covers the base specification for OAI-PMH. `#1850 <https://github.com/BirkbeckCTP/janeway/pull/1850>`_

Crossref
^^^^^^^^
* Our crossref citation depositor now converts DOIs in URL format to prefix/suffix as this it the only format crossref accepts. `#1869 <https://github.com/BirkbeckCTP/janeway/issues/1869>`_
