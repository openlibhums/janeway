Personally Identifiable Information
===================================

Janeway collects personally identifiable information (PII) from users during registration and the assignment of authors to articles. This information is stored in `Account` and `FrozenAuthor` records.

FrozenAuthor Model
------------------
The `FrozenAuthor` model is designed to capture a snapshot of author details at the time of submission and publication. The following fields are considered PII:

- name_prefix: This does not identify any individual directly, but could contribute to their identification if combined with other information
- first_name: This directly identifies an individual.
- middle_name: This does not identify any individual directly, but could contribute to their identification if combined with other information
- last_name: This directly identifies an individual.
- name_suffix: This does not identify any individual directly, but could contribute to their identification if combined with other information
- frozen_biography: This does not directly identify an individual but may contain identifiable information.
- institution: This does not identify any individual directly, but could contribute to their identification if combined with other information
- department: This does not identify any individual directly, but could contribute to their identification if combined with other information
- frozen_email: This directly identifies an individual.
- frozen_orcid: This directly identifies an individual and links to their scholarly profile.
- country: This does not identify any individual directly, but could contribute to their identification if combined with other information

Account Model
-------------
Janeway implements a custom `Account` model that holds profile information.

- email: This directly identifies an individual.
- username: This can be used to directly identify and contact an individual. The username is not editable and copies the email field.
- first_name: This directly identifies an individual.
- middle_name: This does not identify any individual directly, but could contribute to their identification if combined with other information
- last_name: This directly identifies an individual.
- biography: This may contain identifiable information.
- orcid: This directly identifies an individual and links to their scholarly profile.
- institution: This does not identify any individual directly, but could contribute to their identification if combined with other information
- department: This does not identify any individual directly, but could contribute to their identification if combined with other information
- twitter: This could directly identify an individual and link to their social media profile.
- facebook: This could directly identify an individual and link to their social media profile.
- linkedin: CThis could directly identify an individual and link to their professional profile.
- website: This could directly identify an individual and link to their personal or professional identity.
- github: This could directly identify an individual and link to their programming contributions.
- profile_image: This could directly identify an individual.
- country: This does not identify any individual directly, but could contribute to their identification if combined with other information


Information Sharing
-------------------
When an article is accepted and published some PII is publicly shared. This is necessary for indexing, preservation and attribution of publications. In Janeway, data is disseminated via the REST API, OAI-PMH feed and directly to external organisations like Crossref, DOAJ and Portico.

Below are some examples of the data that Janeway shares directly with external organisations when their integrations are enabled.

Crossref
~~~~~~~~
When Crossref integration is enabled, the following personal information is shared:

- Author names
- Correspondence author email
- Institution and department
- ORCID
- Country

DOAJ
~~~~
When the DOAJ Transporter is enabled, the following personal information is shared:

- Author names
- Institution and department
- ORCID
