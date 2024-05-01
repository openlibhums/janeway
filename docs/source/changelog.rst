Changelog
=========

Release notes have moved to [Github](https://github.com/BirkbeckCTP/janeway/releases)

v1.5.1 Archer
-------------
Upgrade Notes
^^^^^^^^^^^^^

To run this upgrade, you can use Janeway's built-in script (.update.sh).
There are no expected backwards-incompatible changes when upgrading from 1.5.0

What's Changed
^^^^^^^^^^^^^^
* Recognises .avif as a valid image mime by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3495
* [XSLT] Allows styled-content to declare custom CSS classes by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3494
* Adds support for fig/alt-text to JATS XSLT by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3493
* Fixes a typo in our Readme file by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3520
* Update requirements for Python 3.10 compatibility #3524 by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3525
* Remove recaptcha_init templatetag by @yakky in https://github.com/BirkbeckCTP/janeway/pull/3507
* Added a janeway db bases SessionStore and overwrite clear_expired by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3476
* Update docs/requirements.txt to pin a few module versions by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3485
* Merge b_1_5_0 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3532
* Bump sqlparse from 0.2.3 to 0.4.4 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/3499
* Bump django from 3.2.18 to 3.2.19 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/3539
* B 1 5 0 v2 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3540
* 3316 improve sitemap generation by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3535
* B 1 5 0 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3552
* #3288 update generate_preprints command and tweaked preprint.html. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3443
* #3188 issue_add_articles now uses the active_objects manager by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3460
* #3533 the Logs, Documents and More dropdown now has a link directly to the Edit Metadata page by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3534
* #3404 adds some enhancements to the repository submission file upload by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3479
* #3502 DOI edit and add buttons will no longer be shown to authors on the article metadata page. Text on the identifiers section has also been updated by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3513
* Adds a check_plugin_exists function to utils.plugins by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3553
* Disable is_secure URL builder checks when DEBUG is on by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3554
* #3491 editors will no longer see the Review Form ID field and the slug field has been removed entirely by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3536
* Press managers can customise some elements of journal footers by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3531
* 3427 automated reminder help text has been update to make the function of the Review (Accepted) review type clearer by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3538
* Increases the journal code CharField max_length to 40 by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3546
* Peer review invite  by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3541
* #3289 remove ID from section __str__ by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3459
* Fix a SASS bug that unset default colors on OLH theme by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3530
* Use raw ID fields for files in a few spots for quicker loading by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3527
* Fix bug that reloaded an email template without user confirming by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3518
* Fix bug with section display on submissions page by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3523
* 3101 article figures now enlarge with lightbox as the default on-click effect by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3537
* Add a test for whether /usr/bin/crontab exists, before attempting to run install_cron. Warn if crontab not found. by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3461
* Updates the JATS 1.2 XML document with additional information by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3506
* Make sure review visibility warning only shows up when it should by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3519
* Issue assignment clarity by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3511
* Modify article pages for all themes to support proofing accuracy by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3471
* Editors and Section Editors can now access the account API endpoint. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3544
* Uses Django's SQL compiler to sort FT search results by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3575
* #1471 pass decisions through to the warning view so it can redirect the user properly by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3570
* Bump requests from 2.25.1 to 2.31.0 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/3566
* BirkbeckCTP/typesetting#184 galley.type and galley.file.mime_type will now be synced when a galley.file changes by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3580
* Fix bug that prevented BookLink from loading in admin by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3583
* B 1 5 0 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3590
* Fixes a bug where the footer in material theme would not be fixed at the bottom of the page by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3585
* Order news by sequence and display date by @gamboz in https://github.com/BirkbeckCTP/janeway/pull/3600
* Fixes an issue were email settings were empty on Docker by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3619
* #2214: Re-instate default-li for submission items on material theme by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3642
* Remove "Incomplete submissions" from repository manager by @alainna in https://github.com/BirkbeckCTP/janeway/pull/3626
* Bump django from 3.2.19 to 3.2.20 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/3623
* Fix bug that kept small caps from being applied by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3603
* Snapshot and update authors on acceptance before deposit #2702 by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3592
* 2986 fixes an error that caused edit_metadata to fail when additional fields were present. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3568
* 965 the old submission_competing_interests has been removed, this is controlled by submission configuration by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3569
* #3348 comments to the editor field has been moved to the end of the submission flow by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3581
* Deprecate run_upgrade command  by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3696
* Fix invalid anchor tag #3697 by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3698
* Add menu option for press-level media manager #3144 by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3699
* Modify funder help text in submission migrations by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3704
* #3627 the email sent to editors when an author completes revisions is now a template and is logged correctly by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3655
* #3618 the review preview form now renders correctly accounting for display settings by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3649
* #3616 reviewers can now access reviews in any of the accessible review stages. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3660
* #3099 reminder emails are now logged by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3648
* #3604 Updated spelling of anonimity to anonymity. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3613
* #3598 the press manager index no longer errors when an article is orphaned from its journal. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3614
* Upgrade materialize by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3594
* #3586 fixes the display of the Review Files section when there are no files and its widescreen display by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3587
* Auto-generated table of contents for articles (TOCs) can now have HTML in them. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3526
* Add preprint API endpoint by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3166
* #3665 the Draft Decisions model now uses the correct decision types. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3666
* #870 removed the is_checkbox monkey patch by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3615
* Rework article list as class-based view by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3597
* 2445 review response letter & sharing peer reviews by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3610
* Use django_countries library by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3582
* Use environment variables for defaults for the install_janeway management command by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3324
* #2444 added a new setting that controls the appearance of a list of reviewers that have previously completed a review in a past round for the current article. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3591
* #3652 when an editor views the submission form they will now see information about which sections are not open for public submission. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3654
* Fixes an odd merge issue. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3720
* Support copy-paste in rich-text fields and fine-tune editing window by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3446
* Password length requirement is displayed properly on all themes. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3700
* #3643 when editing a single setting using the edit_key view unchecking a boolean now works as expected. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3651
* #3240 when a mailgun email is logged as failed or bounced it will now send an email to the actor (if they are staff, editor or repo manger) and log that it was sent by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3512
* Fix article list view access by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3723
* 3630 the Live Article link in LDM will now link to the remote url when is_remote and remote_url are set by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3650
* Pin urllib3<2 due to compatibility issues with requests by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3737
* Apply scrollbar to long unbroken MathJax lines #3753 by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3754
* XSLT 1.5.1 Fixes & Updates by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3750
* Bump pillow from 9.4.0 to 10.0.1 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/3748
* Fix KeyError when logging with orcid and name is not publicly available by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3758
* Bump pdfminer to fix bug with blank password on PDFs by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3757
* Allow blank preprint version titles so that they can be edited in admin by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3759
* #3716 next_workflow_element will no longer error out when an article is published. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3718
* 3705 Adds a signal that will create a directory in src/files when a new journal is created. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3706
* #3728 editing a copyedit assignment will now success and, if it fails, it will disply an error. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3729
* #3733 wording on the projected issue page has been updated, documentation for how this works has also been added. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3734
* #3728 when editing a frozen author record the Add Author button now works as expected. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3730
* #3486 DOI batch deposit timestamps are now generated in the view using datetime rather than the now templatetag which uses timezone. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3721
* Removed light and wave effects from headers in the material theme. These serve no real purpose and stop users from copying the title text easily. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3668
* #3684 the merge users documentation has been updated and now includes an animated gif. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3686
* Adds an edit metadata button to the unassigned article/editor assignment page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3687
* Altmetric badges will now display as expected on the material theme. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3680
* Author review text will now display properly when checked by an editor by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3739
* Include GET parameters when redirecting after login #3701 by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3702
* Ensure article titles are marked as safe consistently by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3543
* When editing repository settings repository managers can choose to save and stay on the current page or save and move to the next step. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3667
* #3487 when requesting revisions the Editor Note field is now optional and is no longer inserted into the outgoing request email. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3681
* #3731 mailbox labels are now wrapped in quotes and sanitize_from is appllied to journal and user names by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3762
* #3372 the issue title is now cached in all available languages, or the default if none are enabled. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3663
* prevents None from appearing in Add Review Assignment by @hachacha in https://github.com/BirkbeckCTP/janeway/pull/3764
* Repository comments will now display properly in the manager interface by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3647
* Added some info about OAI to docs by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3636
* #3423 moved comments box under preprint iframe. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3645
* 3638 orcid pattern update by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3646
* Adds a new form and widget that implements CC and BCC fields for all emails by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3121
* Move command calls from migrations to update script by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3787
* Update journal_defaults.json - typofix1 by @S-Haime in https://github.com/BirkbeckCTP/janeway/pull/3800
* Pil antialias change 151 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3817
* Limits ithenticate requests to those articles with no score stored. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3805
* Updates how_to_cite generation. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3804
* #3802 rework the clean theme's editorial page layout. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3803
* Fix bug causing None to appear in HTML by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3789
* 3672 adds a new setting to the news homepage element to allow the display of images, works for OLH and Material themes. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3818
* #3675 repository managers can now delete comments. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3814
* #3673 when creating a new row include the data-equalizer to ensure that blocks are the same height. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3813
* 3670 adds support for multiple themes in repositories and fixes original preprint templates from the OLH theme. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3811
* #3674 adds a new option to repository reviews allowing reviewers to make a clear recommendation to repo managers. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3815
* 3491 moves the generation of the default review form to a method of the Journal object so that it can be easily called. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3824
* 3828 EditorArticleInfoSubmit now checks if the section field is present before altering it. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3830
* #3844 fixes a bug where abstracts can appear in the document header. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3846
* Remove superseded class definition by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3870
* Remove required from some form BleachFields by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3871
* 3864 fixes a bug that causes a server error when accepting a draft decision by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3885
* #3872 search bar label for now matches the search field ID by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3880
* #3877 when searching repoistory objects by author results are now limited by repository. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3879
* Disable bleach by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3902
* Provide missing template variable in modal by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3869
* XSLT fixes and changes noted on the migration of UCL by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3910
* #3883 the journal article page is now sorted correctly by default by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3884
* #3888 Updated the preview peer review form to hide the open peer review section when setting is disabled. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3889
* #3849 added a database agnostic way to get a list of reviews based on distinct reviewers by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3876
* #3873 request.FILES now passed to EmailForm when sending a user email. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3875
* #3866 automatic editor assignments now fire as expected by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3882
* Flagged missing strings for translation in publicly available interfaces by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3960
* Flags more public strings for translation by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3966
* XSLT: Render ack/title elements by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3968
* Fixed a bug where PDF/XML article files could be downloaded before an article is published by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3978
* Fixed a few HTML tags that where not closed properly on the clean theme by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/4003
* Adds support for removing formatting when copying and pasting from word into article abstract and other fields by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3983
* Adds mising close tag to the tinyMCE script tag by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/4033
* Stops multiple galley image files with the same name from being loaded in the edit galley interface. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/4032
* Added support for clearing fromatting from pasted inputs onto the user page data by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/4038
* Fixes additional whitespace being added after italics and bold to HTML galleys  by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/4044

New Contributors
^^^^^^^^^^^^^^^^
* @yakky made their first contribution in https://github.com/BirkbeckCTP/janeway/pull/3507
* @S-Haime made their first contribution in https://github.com/BirkbeckCTP/janeway/pull/3800

**Full Changelog**: https://github.com/BirkbeckCTP/janeway/compare/v1.5.0...v1.5.1

v1.5.0 Torres
-------------
Upgrade Notes
^^^^^^^^^^^^^

To run this upgrade, you can use Janeway's built-in script (.update.sh).

On this version of Janeway we have bumped the version of Django from 1.11 to the most recent LTS version 3.2. As a result of multiple
backwards changes, there have been a lot of rewrites of old code involved. Any installed plugins do need to be updated for compatibility
with this new release as well, so we recommend upgrading your plugins first, before running the .update.sh script

What's Changed
^^^^^^^^^^^^^^

* Exposes the XML url as a meta tag for indexers (Google Scholar) by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3437
* Django three two rebase by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3438
* Bump django from 3.2.16 to 3.2.18 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/3439
* Updated for hijack 3.x and tweaked to retain current layout/style. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3329
* Fixes the check for is_anonymous in utils.models.add_entry by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3347
* #3326 fix query to get the latest round number by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3341
* Switched to a production version of django-bootstrap4 by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3343
* Guest Editors can now be sorted. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3368
* #3342 the current Janeway version now displays in the bottom left hand of the manager nav, placement of the languange switcher is now common to all Site types. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3344
* Fixes mutable_cache_property for django 3.2 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3410
* Fixes some of the test failures on the 3.2 branch by bumping the version of model translations. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3399
* Dropped Raven as a core requirement, added docs for sentry error capturing by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3405
* Adds a new command that will clear a janeway install's cache. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3400
* Bumps requirements based on depandabot alerts. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3398
* After installation is complete, clear the cache so that the install is fresh by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3401
* #3420 adds time 23:59:59 to the oai feed until date when present by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3421
* #3428 revives the contact_info attrbiture as a Setting and uses it on the Contact page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3431
* Fixes URL resolver for django-hijack on django 3.2 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3433
* Added a note to recommend that when editing frozen author data editors make email and ORCID changes at the account level. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3390
* #3230 removes broken button on revision and copyedit replace file screens by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3417
* Overhaul admin views to support searching and browsing by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3345
* Journal manager role by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3374
* Oai datetime support by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3435
* Adds some basic tests for the frontend by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3429


**Full Changelog**: https://github.com/BirkbeckCTP/janeway/compare/v1.4.4...v1.5.0-RC-1

v1.4.4 Apollo
-------------
Upgrade Notes
^^^^^^^^^^^^^

To run this upgrade, you can use Janeway's built-in script (.update.sh). There are no newly introduced configuration steps required.

This minor release includes a few bugfixes and improvements on features newly introduced in v1.4.3


What's Changed
^^^^^^^^^^^^^^
* Add pagination for Django REST Framework to Janeway global settings by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3301
* #3302 hamburger menu now works on Repository mobile interface. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3303
* 3304 reader notifications bugfixes by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3306
* Handle error when nose is not present by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3308
* Add swagger and redoc docs to api by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3300
* Author address won't be shared as reply-to on submission acknowledgements by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3312
* 3309 Add template fragment cache to metrics block on /repository/manager by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3310
* Fixes preprint generator by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3314
* #3311 the Active Submissions view will no longer show archived articles. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3313
* XSLT now allows ref/label nodes to be rendered as HTML by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3320
* Improved performance of repository manager page by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3315
* Updated custom replyto and added a catch incase reply_to is not a tuple or list by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3321
* typo :) by @gamboz in https://github.com/BirkbeckCTP/janeway/pull/3330
* #3322 articles should no longer be stalled when funding is enabled. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3325
* Update to reviewer.rst by @justingonder in https://github.com/BirkbeckCTP/janeway/pull/3336
* The manage workflow stage link is now available to editors by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3349
* Display the issue DOI URL on the issue page when it is available by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3354
* Changes ableist terminology around peer review anonymity by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3353
* Updates localisation files by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3388
* Add RSS feed for preprints by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3391
* Name of CC-ND licenses changed to NoDerivatives by @gamboz in https://github.com/BirkbeckCTP/janeway/pull/3397
* Adds the base structure and migrations to support en-us locale by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3389
* Fixes a bug where metrics were being stored agaisnt the wrong type of galley by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3395
* Refactor tests to eliminate naive datetime warnings by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/3381
* Fixed an issue where articles with a publication title override where not using in the "how to cite" block by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3406


v1.4.3
------

This version of Janeway includes various new features and bugfixes.

Upgrade Notes
^^^^^^^^^^^^^
As normal run the ``.update.sh`` command.

DOIs
^^^^

* Added support for title-level DOIs
* Added support for issue-level DOIs
* Updated the DOI Manager page to make it scale better

Peer Review
^^^^^^^^^^^

* The interface for making reivews available to authors has been updated to make it easier to use and easier for editors to see the current status
* Editors can now see reviews in the draft decisions interface
* Where a peer review is open, and the reviewer gives explicit permission, that review can now be displayed on the article page
* Additional metadata is now available to peer reviewers, including due date

Workflow
^^^^^^^^

* We've made various updates to make the workflow more user-friendly
* Editors can now archive an article at any point in the workflow
* When an editor completes a workflow stage, instead of being redirected to the dashboard, they will now move to the next workflow element
* Workflow notification pages now display custom subjects properly
* Popup contact email forms can now have attachments
* Editors can now unreject articles and can move articles that are stuck in "Accepted" onto the next workflow element
* Various task completion tasks now ask the user to confirm the requested action
* Whenever you send an email using Janeway, you get a small green bar in the bottom right confirming "Email sent"

Repository
^^^^^^^^^^

* There are various fixes around the repository system including fixes to make repository multi-tenancy work better

Other
^^^^^

* Update to article XSLT properly renders footnote numbers and allows footnotes to be referenced multiple times
* Update to article XSLT allows rendering xrefs in footnotes
* Articles can now export references in Bibtex and RIS

Changelog
^^^^^^^^^

* #2994 adds href to the manage reviewers link on the add reviewer page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2995
* Add confirmation pane to author-facing task submission buttons by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2950
* 3015 editors can now send author copyedit review notifications if they are initially skipped. Editors can also delete uncomplete author reviews with an optioinal email notification. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3049
* #2847 replace hard coded next stage text when completing copyediting with calculation of next stage. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3023
* Enable preprint moderators to un-reject preprint by @alainna in https://github.com/BirkbeckCTP/janeway/pull/3067
* #3057 Fix hard-coded article IDs by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3058
* #3052 Fixes default templates by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3053
* b_1_4_2_1 merge by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3102
* #3109 full text indexing will now work as expected for HTML with a body tag. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3110
* #2320 the OLH theme will now display text when an article is not peer reviewed. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3013
* Document and test reply-to setting by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3044
* Fix logic on issue assignment during prepublication checklist by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3042
* Bugfixes for popular and featured homepage elements by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3040
* Fix some typos by @fingolfin in https://github.com/BirkbeckCTP/janeway/pull/3003
* Add Undo Article Rejection button on archive page by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2996
* Debug email subject settings by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3030
* #2840 added setting to form, updated to work on form. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3035
* Copyeditors can now see the article ID on the list and detail pages. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2990
* Fix an issue where table footnotes would lead article footnotes to no longer link correctly by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2988
* Adds controls for handling articles in Accepted stage by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3060
* Make the translation markup changes identified in PR #2974 by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/2984
* 1170 editors can now sort an issue's articles by date_published, title, article number or page numbers by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3012
* Let section editors see more list views by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3115
* #3074 the author section of the dashboard has been split to show published articles independently, datatables have been added and sections are ordered properly. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3083
* #3063 remove the enable_digest field from themes as not all themes fail gracefully by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3064
* Privacy policy link on the clean theme's registration page now renders the correct override. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3092
* 3059 when an editor completes a workflow element they will automatically be moved onto the next one rather than being directed to the dashboard by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3069
* Adds a warning when manually changing an article stage via admin by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3119
* #3112 allows staff to override the journal description when displaying it on the press journal list page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3113
* #3038 when the keywords page is enabled, readers can click on article keywords to see a list of articles that use that keyword. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3050
* #2755 added the Article Rights field to the View and Edit metadata pages. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3019
* #2814 updated the decision page's skip button text to make it clearer. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3021
* #2857 when a journal disables submission they can now set a custom message. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3031
* #2851 added link to toc header for material. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3036
* #2969 staff, editors and section editors can bypass funding_is_enabled decorator by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3029
* Editors will be warned when they attempt to assign a task to a user whose account is not active. by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3054
* 2841 fixes article links on profile pages by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3124
* #2904 fixes an issue that caused modified dates for File objects not to show up by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3032
* Fixes a bug with page ranges that caused articles not to appear in lists by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3132
* Fixed a bug preventing output of internal links to references from footnotes via XSLT by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3129
* Bump lxml from 4.6.5 to 4.9.1 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/2985
* #3112 fixed a typo, made messages translatable by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3127
* Standardize admin fonts to Open Sans by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3135
* 2937 adds DOI pattern validation to repository submission and update. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2944
* 2935 various multitenancy bugfixes for repositories by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2946
* Control user button now also appears on the search user interface. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3065
* #2820 Accounts now have a suffix field that will be snapshotted into Frozen Authors by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3084
* Makes OIDC use the press url path and adds ?next for a redirect. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3095
* Two submission settings were duplicated on the settings page, the duplicates have been removed. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3094
* #2711 review due dates are now in the default invitation and on the review page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3018
* #2819 adds description to Review Files block to avoid confusion and adds the latest manuscript and figure files inline below a revision request. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3020
* Adds support for Issue and Journal DOIs to Crossref Integration by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3128
* #3138 Fixes bug that put 'collection' in issue urls by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3139
* The Competing Interests field can now output HTML. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3103
* Article citations can now be downloaded in RIS and BibTeX format for ingestion on citation managers. by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3118
* Fix conflicts between core/0074 migrations by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3141
* RSS feed titles and descriptions are now not terrible. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3123
* Fix test_article_image_galley by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3143
* Added new settings to disable article thumbnails and article large image independantly  by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3120
* #2875 oai pmh endpoint for preprints by @everreau in https://github.com/BirkbeckCTP/janeway/pull/3098
* XSLT: Allow footnotes to be referenced multiple times by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/3117
* Fix bug that duplicated issue title by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3148
* #2934 repositories can now select active licenses from those available. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2955
* 518 adds new reader role to which users can add themselves, they will then receive notifications when new articles are published by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2943
* Removed status logic from manager_review_status_change setting. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3000
* Add open peer review. #141 by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2602
* #2737 Added new archive stage. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2929
* #2028 adds a feature flag to disable the Reviews block on the author's article page before acceptance/rejection by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2945
* Test fixes. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3151
* #2992 installations and journals can now set which theme is used as the base theme by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2998
* Added clear script prefix. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3152
* Issues that are not yet published can no longer be set as a journal's current issue. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3062
* Allow the press image to be a non-svg by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3071
* 2954 updates the review visibility settings to give them a unified style. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3016
* Added fix for failing test by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3153
* Updates for #3155 and #3086 by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3156
* Test fixes for version 1.4.3-release-candidate-0 by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3158
* Merge migrations for version 1.4.3 by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3154
* #3159 Fix bug that removed author when searching funders by @joemull in https://github.com/BirkbeckCTP/janeway/pull/3162
* Added keywords and meta block to OLH theme by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/3161

**New Contributors**

* @fingolfin made their first contribution in https://github.com/BirkbeckCTP/janeway/pull/3003
* @everreau made their first contribution in https://github.com/BirkbeckCTP/janeway/pull/3098

**Full Changelog**: https://github.com/BirkbeckCTP/janeway/compare/v1.4.2.1...v1.4.3-RC-1

v1.4.2
------

Upgrade Notes
^^^^^^^^^^^^^
If you intend on enabling full-text search, see the specific notes about this feature below prior to upgrading.

The ``upgrade.sh`` script should then cover the usual upgrade procedure.

Since this release includes a fix for the sitemaps, we recommend re-generating them with ``python src/manage.py generate_sitemaps``
as documented in https://janeway.readthedocs.io/en/latest/robotsandsitemaps.html#sitemaps after the upgrade is completed.


Full-text Search
^^^^^^^^^^^^^^^^
This version of Janeway includes built-in support for full-text search. There is a feature flag controlling if this new feature should be enabled for an entire installation.

If you intend on enabling this feature, we recommend setting the following variables in your `settings.py`:

`ENABLE_FULL_TEXT_SEARCH = True`

For installations running PostgreSQL, it is also recommended to enable the following setting:
`CORE_FILETEXT_MODEL = "core.PGFileText"` (More details at https://janeway.readthedocs.io/en/latest/configuration.html#full-text-search )


OIDC
^^^^
Janeway now supports authentication via OIDC. If you would like to enable this new authentication system, we recommend having a look at the configuration instructions in the documentation:
https://janeway.readthedocs.io/en/latest/oidc.html


Changelog
^^^^^^^^^

* Add base class for filterable class-based view by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2855
* Added h5 and h6 styling for article-body by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2850
* 2852 updates to bring the clean theme article page inline with OLH and material by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2854
* #2649 merge users page now uses the API to search and runs faster by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2830
* Make Account.institution and FrozenAuthor.institution optional by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2740
* Allows Competing Interests to be edited from the Edit Metadata pane by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2745
* #2831 added a decorator to stop users accessing submission pages afte… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2832
* Fix OAI not filtering by from/until by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2860
* Fixes captcha display on the disabled front end contact form. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2867
* Removes remote journals from press sitemaps by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2871
* 2869 adds additional filters to limit the scope of views to the current repository where required by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2870
* Merge of v1.4.1.1 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2872
* JATS: Added support for title tags in list-item objects by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2881
* Material Theme: the font weight for tags is now heavier to show difference from normal text by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2880
* Custom fields displayed in the article will now support HTML. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2877
* Fix wrong copyeditor decision sent on notifications by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2884
* Fixed a server error when deleting duplicate frozen authors by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2883
* Remove warning about non-public declined review assignments by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2882
* Adds a data migration that deletes blank keywords/disciplines by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2878
* Only a comment about the field Journal.description not being used. by @gamboz in https://github.com/BirkbeckCTP/janeway/pull/2903
* Bump pyjwt from 1.6.1 to 2.4.0 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/2891
* Adjusted Issue.code so it can be indexed by MySQL by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2909
* Fix an error on subject retrieval when generating emails outside of a request context by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2902
* #2793 added eq-height to editorial team page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2901
* Removed duplicate kanban cards for production and proofing. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2900
* Adds support for JATS continued-from. Credit to @mauromsl by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2893
* #2894 renders the Clean theme footer in a more responsive manner. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2895
* #2356 mobile download links also now show near the top of article pag… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2899
* Allow editors to attach files on the decision page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2889
* JATS: <title> tags inside a glossary now rendered as an by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2887
* #2863 JATS: adds classes for attrib and addresses by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2885
* Added support for full text search of database fields and PDF/XML galleys by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2908
* Git-ignore emacs' backup files by @gamboz in https://github.com/BirkbeckCTP/janeway/pull/2913
* Deduplicate identifiers by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2896
* 2835 Repository managers can copy a preprint into a journal stage by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2879
* #2658 fixes misconfiguration of mathjax on material theme by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2886
* Added GA Four support to all themes. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2865
* #2584 adds support for OIDC login. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2824
* Updating the author dashboard text: owner->submitting author by @alainna in https://github.com/BirkbeckCTP/janeway/pull/2914
* 2781 Janeway now stores ORCIDs in a standard format of 0000-0000-0000-000X by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2906
* Added docs for plugins, events and hooks. This is a WIP but more usef… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2912
* 2834 Repository managers can invite people to comment on preprints/postprints, similar to peer review by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2864
* KBART export will now filter out remote and hidden journals. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2918
* DOI Manager by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2888
* Allow search results to be orderered by relevance (Postgresql) by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2925
* #2839 enable_digest is now hidden on profile forms. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2919
* #2227 Reviews now display on the draft decision page to assist editor… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2916
* Bump pillow from 7.1.0 to 9.0.1 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/2796
* #2654 the journal manager now displays the janeway version in the bot… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2921
* #2838 merge users now shows if a user is active or inactive by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2923
* #2777 adds a modal intermediary warning users before creating a new r… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2922
* Adds a new homepage element that renders a search bar by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2907
* #2450 Sitemaps now have a stylesheet to make them human readable. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2917
* Doi Manager style adjustments by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2926
* #2518 popup email windows now support attachments by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2920
* Updated the submission review and submission details layouts by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2915
* Fix dropdown from overflowing the screen in review page by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2928
* Adds missing translation tags for the text 'and' by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2932
* Bump Version v1.4.2 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2927

v1.4.1
------
Version 1.4.1 introduces repositories, the brand-new repository system for Janeway.

Upgrade notes
^^^^^^^^^^^^^

With this release of Janeway, there are a couple of new commands to generate the `robots.txt` and `sitemap.xml` endpoints.

After running the upgrade script `upgrade.sh`, you should run `python src/manage.py generate_robots` and `python src/manage.py generate_sitemaps`.

Sitemaps will be regenerated on a daily basis as per the configuration of the cron tasks installed by Janeway.

What's Changed
^^^^^^^^^^^^^^

* Revise object-related text for repository pages. by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/1739
* Port Lando configs from Master to preprint-remodel by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/1733
* 1664 preprint page by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1765
* Updates the homepage of the material theme. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1762
* 1736 multi subject by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1774
* #1767 added paginator to base of page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1775
* 1633 search feature by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1766
* add capfirst builtin to repository list navigation in OLH and Material theme repository nav templates by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/1776
* add reminder to restart to the update script by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/1777
* #1769 decline now redirects to the decision email page as it should a… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1782
* 1770 press email base domains by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1781
* 1773 log page by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1783
* #1784 added link to license where present. abstracts are now truncate… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1786
* #1684 updated fields interface. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1788
* Backport commits from PR1755 to ensure the debug toolbar can coexist with tests by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/1791
* Preprint remodel model changes by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1799
* WIP for preprints remodel: Supplementary files #1590 take 2 by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1789
* Preprints: add repository.custom_js to every page by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1814
* Added order_by publication date for list and home page view by @myucekul in https://github.com/BirkbeckCTP/janeway/pull/1813
* [Preprints]: sitemap refactored like press.index by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1815
* [Preprints] minor template bugs - fix escaping for custom_js and broken download link by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1817
* Some New Settings! by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1819
* 1590 supp file manager by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1822
* #1825 fixed typo. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1826
* 1823 Adds a submission agreement statement to the submission page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1824
* [preprint] make the "Additional Metadata" header conditional by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1833
* Made some minor improvements by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1834
* Repository manager fix by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1841
* Closes #1844 - pops submission agreement and editor comments in manag… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1845
* 1842 admi dash load by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1846
* [preprints] links on repository manager dashboard should work by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1860
* use the count of objects from the paginator.page object for the list of preprints by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/1872
* A bit of Django wizardry will pass author select over to SQL where it… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1892
* Add Self as Author button: ensure the user's orcid is copied, too by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/1885
* 1898 added subject page and made subject filtering bette by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1899
* [preprints] add subject link to nav-mobile by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1904
* Makes preprint versions better on preprint page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1901
* Fixes registration's crap errors by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1900
* #1911 fixes the PreprintInfo form. Adds textarea form element. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1914
* #1893 only assign an owner if there isn't one already by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1920
* 1873 added a base solution for this problem. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1891
* [preprints] merge some migrations by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/1931
* Embedded pdfs are now excluded from Download Metrics. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/1944
* Better CSS selector for subjects' <ul> by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2030
* [preprints] Preprint remodel metadata edit bug by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2027
* [preprint] -- author rework -- more tolerance for missing values by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2084
* Correct Pending Updates table heading by @justingonder in https://github.com/BirkbeckCTP/janeway/pull/2124
* preprint with 3+ authors #2090 by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2237
* Hotfix PUBD-209 section editors should be able to download assigned files by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/2293
* Preprints author rework by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2079
* #1940 allow authors to add a pub DOI when updating metadata. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2348
* add "View Live Article" link as per #2424 by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2455
* #2090 completes this and closes #2090 by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2440
* Add preprint_doi to repository/article template by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/2468
* check is_published for View Article moderator page (preprint-merge) by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2483
* Add DOI and Preprint DOI to Author_Article template by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/2482
* Tweak the display of the preprint_doi field in repository author_article template by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/2489
* #2187 support ordering keywords for preprints. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2471
* 2310 bugfix by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2439
* Work on #2278 and #2273 by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2437
* #2264 allow authors to delete incomplete preprints. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2438
* #2447 added check that preprint has authors. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2448
* merge migraions after master merged to preprint-merge by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2501
* [preprint-merge] 'block' tag with name 'css' appears more than once by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2503
* Delete and order by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2507
* Move call for ON_WORKFLOW_ELEMENT_COMPLETE to follow article.save by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/2516
* reduce number of columns in header for DOIs on author_article template by @hardyoyo in https://github.com/BirkbeckCTP/janeway/pull/2524
* Preprints: add a full_name to preprint.Author by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2529
* author->acct last name update by @alainna in https://github.com/BirkbeckCTP/janeway/pull/2570
* [preprints] use `first.full_name` rather than `all.0.author.full_name` by @tingletech in https://github.com/BirkbeckCTP/janeway/pull/2578
* Jats tables by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2628
* Added keyword input on jats import by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2636
* Preprint merge by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2345
* Swapped hardcoded application/xml filter for XML_FILETYPES from core.… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2630
* Remove reviewer name to make this simpler for Editors by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2646
* #2637 updated docs for managing a typeset file by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2640
* Abstract is marked safe by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2638
* Remove success class from buttons by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2647
* Bump lxml from 4.6.3 to 4.6.5 by @dependabot in https://github.com/BirkbeckCTP/janeway/pull/2664
* Review page uses the correct order of authors by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2669
* #2652 added css to break the contents of these TDs by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2653
* #2619 #2026 css updates. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2623
* Changed the version number. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2611
* #2567 hide submission links when submission is disabled. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2614
* #2620 added a --force_update flag to load_default_settings by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2625
* #2622 records email subjects in logs and fixed a bug by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2624
* #2595 added he for <bio><title> by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2617
* Add support email settings for manager page by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2631
* 2588 css update by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2615
* Add frozen_biography and biography() to FrozenAuthor by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2660
* #2587 updated xslt by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2616
* Adds an id to the cms container on all themes by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2688
* Journal title on navbar controlled by a setting by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2687
* Allow images as SVG to be used across journal/repository pages by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2683
* Allow combining domain and path modes by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2684
* Adds a code field to Issue allowing for verbose urls by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2689
* #2671 #2672 fixes both these bugs. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2691
* Removes link from journals with no current issue by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2690
* #2680: XSLT fix fn links colliding with tables by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2681
* Adds a second review form element. This ensures save works when one e… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2692
* Update author dashboard messaging by @alainna in https://github.com/BirkbeckCTP/janeway/pull/2695
* Render django-hijack banner when DEBUG is False by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2698
* #2585 removed excess <p> tags. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2618
* #2373 added the contact form to submission only. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2613
* Fix DOI links in dashboard view by @alainna in https://github.com/BirkbeckCTP/janeway/pull/2696
* Remove the sitemap link as its for comps not people by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2463
* Fix wrong URL in fc238996 by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2703
* Added missing import by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2704
* Fix wrong URL on footer's press logo by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2705
* Fix bug on press contact page. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2707
* Tweak the FN layout to make scrolling better by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2709
* Add default journal support message to press manager view and template by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2686
* #2708 alters completed_reviews_with_decision to have correct logic. A… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2710
* #2627 added a new email for authors post revision. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2639
* Make file submission help text a setting by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2634
* #2697 added a migration to update email templates of review_accept_ac… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2700
* #2581 make drilldown scrollable by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2721
* Add issue order description by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2716
* #2718 added fixes to sidebars by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2719
* Image setting documentation by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2643
* Makes profile image responsive on material by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2725
* Update to docs: copyediting, review visibility, and draft decision by @MartinPaulEve in https://github.com/BirkbeckCTP/janeway/pull/2747
* #1087 Fixes last of four typos--first three were already fixed by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2739
* OAI-PMH JATS support by @MartinPaulEve in https://github.com/BirkbeckCTP/janeway/pull/2720
* Fixes the unclosed br tag. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2742
* Ignore empty p and br tags from empty summernote fields by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2714
* OLH: Changes citation picker to a dropdown on mobile by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2727
* Added a wrapper div to Homepage elements for custom styling by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2726
* wrong indentation and typo by @gamboz in https://github.com/BirkbeckCTP/janeway/pull/2760
* Added date suffix to crossref templates to force a match with thier f… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2761
* Adds support for ISSN override at the article level by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2766
* Adds Custom Reply To address for system emails by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2757
* Prevent empty keywords from being saved when using KeywordModelForm by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2754
* OAI resumptionToken now considers querystring params by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2772
* Fix domain journal url rendering while in browsing from path by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2770
* Fixes Keywords not saving due to cleaned data not being mutable by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2778
* Fix table-caption titles and add common css for JATS list types by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2759
* Display article thumbs on large but not 'only' by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2786
* Author display name handles empty first or last name fields by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2783
* Fix bug so that reminders are sent properly by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2788
* #2612 added new review setting for acceptance warning. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2645
* #1182 Provisional: Remove subtitle from templates and note as depreca… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2773
* Robots & Sitemaps by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2767
* Adds hcaptcha support by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2797
* Add option to display page numbers and article numbers on issue pages by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2780
* Allow author enrolement to be vetted by a staff member by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2758
* Adjustments to JavaScript to avoid TOC interference by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2752
* #1035 updates clean and material to work as press themes! YAY! by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2785
* #2550 Let editors change text in file submission pop-up windows by @joemull in https://github.com/BirkbeckCTP/janeway/pull/2748
* #2800 added overflow for table wrapper. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2801
* db backend names typos by @gamboz in https://github.com/BirkbeckCTP/janeway/pull/2806
* Support multi-graphic figures by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2805
* #2789 if the current user is an editor don't filter sections and lice… by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2809
* #2799 Applies new last modified model to get a better lastmod date for articles. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2804
* #2749 slight tidy up of these templates. by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2807
* #2308 removes odd white space issue in mixed citations. No effect to … by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2808
* #2749 updated docs by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2813
* Avoid exploring same model twice during last_mod calculation by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2815
* items_for_reminder now filters Review and Revision objects by journal by @ajrbyers in https://github.com/BirkbeckCTP/janeway/pull/2821
* OAI: Ensure hidden journals are not shared at the press level by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2827
* Replace HTML entities for their unicode counterparts on article.issue_title by @mauromsl in https://github.com/BirkbeckCTP/janeway/pull/2829

v1.4
----
Version 1.4 makes a move from HVAD to ModelTranslations as well as some bugfixes and improvements.

ModelTranslations
^^^^^^^^^^^^^^^^^
Janeway now uses ModelTranslations to store translated settings and metadata. The setting `USE_I18N` must be set to `True` in settings.py otherwise settings may not be returned properly.

1.4 has support for:

* News
* Pages
* Navigation
* Sections
* Editorial Groups
* Contacts
* Journals
* Article (limited to Editors only, title and abstract)

Support for Welsh (Cymraeg) is included. Support for German, French, Spanish and Italian is coming soon.

General
^^^^^^^
* The backend has been updated to use the Open Sans font.
* The default theme has been removed from core and now has its own repo (https://github.com/BirkbeckCTP/janeway/issues/1895)
* The clean theme is now part of core (https://github.com/BirkbeckCTP/janeway/issues/1896)
* All themes have a language switcher when this setting is enabled (https://github.com/BirkbeckCTP/janeway/issues/2159)
* When an Issue number is 0 it will no longer be displayed (https://github.com/BirkbeckCTP/janeway/pull/2338)
* The register page has been updated to make it clear you're registering for a press wide account (https://github.com/BirkbeckCTP/janeway/issues/2390)
* Author text on the OLH theme is now the same size as other surrounding text (https://github.com/BirkbeckCTP/janeway/issues/2368)

News
^^^^
* The news system can now be re titled eg. Blog (https://github.com/BirkbeckCTP/janeway/issues/2381)
* News items can have a custom byline (https://github.com/BirkbeckCTP/janeway/issues/2382)

Bugfixes
^^^^^^^^
* When sending data to crossref the authors are now in the correct order (https://github.com/BirkbeckCTP/janeway/issues/2157)
* doi_pattern and switch_language are no longer flagged as translatable (https://github.com/BirkbeckCTP/janeway/issues/2088 & https://github.com/BirkbeckCTP/janeway/issues/2160)
* `edit_settings_group` has been refactored (https://github.com/BirkbeckCTP/janeway/issues/1708)
* When assigning a copyeditor Editors can now pick any file and it will be presented to the copyeditor (https://github.com/BirkbeckCTP/janeway/issues/2078)
* JATS output for `<underline>`: `<span class="underline">` is now supported via `common.css` (https://github.com/BirkbeckCTP/janeway/pull/2322)
* When a news item, journal and press all have no default image news items will still work (https://github.com/BirkbeckCTP/janeway/issues/2531)
* Update to our XSLT will display more back matter sections (https://github.com/BirkbeckCTP/janeway/issues/2502)
* Users should now be able to copy content from the alternate citation styles popup (https://github.com/BirkbeckCTP/janeway/issues/2506)
* A new setting has been added to allow editors to add a custom message to the login page (https://github.com/BirkbeckCTP/janeway/issues/2504)
* A new setting has been added to add custom text to the end of a crossref datestamp (https://github.com/BirkbeckCTP/janeway/issues/2504)

Workflow
^^^^^^^^
* We now send additional metadata to crossref inc. abstract and accepted date (https://github.com/BirkbeckCTP/janeway/issues/2133)
* The review assignment page has been sped up, suggested reviewers is now a setting and is off by default (https://github.com/BirkbeckCTP/janeway/pull/2325)
* Articles that are assigned to an editor but not sent to Review now have a warning that lets the Editor know this and has a button to move the article into review (https://github.com/BirkbeckCTP/janeway/pull/2322)
* A new setting has been added to allow editors to hide Review metadata from authors including the Reviewer decision (https://github.com/BirkbeckCTP/janeway/issues/2391)

Manager
^^^^^^^
Many areas of the Manager have been reworked. We now have a better grouping of settings and additional groupings. Reworked:

* Journal Settings
* Image Settings (new)
* Article Display Settings
* Styling Settings

Other areas have been redesigned:

* Content Manager
* Journal Contacts
* Editorial Team
* Section Manager
* The Review and Revision reminders interface has been reworked to make it easier to use. A new reminder type (accepted) so you can have different templates for reminder unaccepted and accepted reviews. (https://github.com/BirkbeckCTP/janeway/issues/2370)


New areas have been added:

* Submission Page Items is a new area that lets you build a custom Submission Page with a combination of free text, links to existing settings and special displays (like licenses and sections).
* Media Files lets editors upload and host files like author guidelines or templates

Plugins
^^^^^^^
* A new hook has been added to the CSS block of all themes - this can be used in conjunction with the new Custom Styling plugin to customise a journal's style. (https://github.com/BirkbeckCTP/janeway/issues/2385)

API
^^^
* A KBART API endpoint has been added `[url]/api/kbart` (https://github.com/BirkbeckCTP/janeway/issues/2035)

Feature Removal
^^^^^^^^^^^^^^^
* The ZIP Issue Download feature has been removed, this is due to the fact that in its current form it does not work and is regularly hit by spiders and bots that cause disk space to fill up. The hope is that we can work out a way to bring this back in the future. The Issue Galley feature remains active. (https://github.com/BirkbeckCTP/janeway/issues/2504)

Deprecations
^^^^^^^^^^^^
* `utils.setting_handler.get_requestless_setting` has been marked as deprecated and will be removed in 1.5.
* PluginSettings and PluginSettingValues are deprecated as of 1.4 - all settings are now stored in `core.Setting` and `core.SettingValue` a migration moved PluginSettings over to core.Setting in 1.4 and uses a group name `plugin:PluginName`.

----------

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
The Users and Roles pages have been updated to:

    * Enrolled Users (those users who already have a role on your journal)
    * Enrol Users (allows you to search, but not browse, users to enrol them on your journal)
    * Roles (now only displays users with the given role)

* One click access is now enabled by default for all new journals (https://github.com/BirkbeckCTP/janeway/pull/2105)


Front End
^^^^^^^^^
* Added support for linguistic glosses (https://github.com/BirkbeckCTP/janeway/issues/2031)
* Privacy Policy links are now more visible on Registration pages (https://github.com/BirkbeckCTP/janeway/pull/2174)

Crossref & Identifiers
^^^^^^^^^^^^^^^^^^^^^^
https://github.com/BirkbeckCTP/janeway/issues/2157
Crossref deposit has been update:

    * Authors are now in the correct order
    * Abstracts are included
    * Date accepted is included
    * Page numbers are included

* Publisher IDs can now have . (dots) in them (https://github.com/BirkbeckCTP/janeway/pull/2173)

Docker
^^^^^^
* When running docker using Postgres a pgadmin container is automatically connected (https://github.com/BirkbeckCTP/janeway/pull/2172)

----------

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
