Personally Identifiable Information
===================================

Janeway collects personally identifiable information (PII) from users during registration and the assignment of authors to articles. This information is stored in `Account` and `FrozenAuthor` records.

FrozenAuthor Model
------------------
The `FrozenAuthor` model is designed to capture a snapshot of author details at the time of submission and publication. The following fields are considered PII:

- name_prefix: Does not directly identify an individual but could be combined with other information to identify an individual.
- first_name: Can be used to directly identify an individual.
- middle_name: Does not directly identify an individual but could be combined with other information to identify an individual.
- last_name: Can be used to directly identify an individual.
- name_suffix: Does not directly identify an individual but could be combined with other information to identify an individual.
- frozen_biography: Does not directly identify an individual but could contain identifiable information.
- institution: Does not directly identify an individual but could be combined with other information to identify an individual.
- department: Does not directly identify an individual but could be combined with other information to identify an individual.
- frozen_email: Can be used to directly identify and contact an individual.
- frozen_orcid: Can be used to directly identify an individual and link to their scholarly profile.
- country: Does not directly identify an individual but could be combined with other information to identify an individual.

Account Model
-------------
Janeway implements a custom `Account` model that holds profile information.

- email: Can be used to directly identify and contact an individual.
- username: Can be used to directly identify and contact an individual. Username is not editable and copies the email field.
- first_name: Can be used to directly identify an individual.
- middle_name: Does not directly identify an individual but could be combined with other information to identify an individual.
- last_name: Can be used to directly identify an individual.
- biography: Does not directly identify an individual but could contain identifiable information..
- orcid: Can be used to directly identify an individual and link to their scholarly profile.
- institution: Does not directly identify an individual but could be combined with other information to identify an individual.
- department: Does not directly identify an individual but could be combined with other information to identify an individual.
- twitter: Can be used to directly identify an individual and link to their social media profile.
- facebook: Can be used to directly identify an individual and link to their social media profile.
- linkedin: Can be used to directly identify an individual and link to their professional profile.
- website: Can be used to directly identify an individual and link to their personal or professional identity.
- github: Can be used to directly identify an individual and link to their programming contributions.
- profile_image: Can be used to directly identify an individual.
- country: Does not directly identify an individual but could be combined with other information to identify an individual.


Information Sharing
-------------------
When an article is accepted and eventually published some PII is publicly shared. This sharing is necessary for indexing, preservation and attribution of publications. In Janeway data is disseminated via the REST API, OAI-PMH feed and directly to some external organisations like Crossref, DOAJ and Portico.

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
