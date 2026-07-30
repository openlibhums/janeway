# Licences

Intellectual property licences are given to articles in Janeway by means of the `submissions.models.Licence` object. Usually these are Creative Commons licences, but press managers and editors can create other licences with custom names, links, and descriptions.

## Journal licences

Journal article licences are particular to the journal. The journal is connected with the `journal` field.

When creating a journal, Janeway loads a default set of licences from a fixture located at `utils/install/licence.json`.

The fixture `core/fixtures/licence.json` is not used.

## Repository licences

Repository licences are not necessarily particular to the repository. They are defined by an empty value in the `journal` field, and whether they’ve been added to `Repository.active_licenses`.

When creating a repository, repository licences have to be manually created and added to the `active_licenses` field on the repository, using the Django admin interface.

## Connections to the press

The `press` field on the licence is typically blank.
