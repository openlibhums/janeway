Changelog
=========

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
