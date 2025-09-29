# Journal visibility and publishing status

Janeway has several mechanisms for allowing editors and press managers to control content visibility and filter data streams for each journal.

The following Journal fields provide the configuration options:

- `Journal.hide_from_press`
- `Journal.status`

## What are some example use cases for these configuration options?

Users may find it tricky to distinguish `hide_from_press` and the "Test" publishing status. But they have to remain distinct for a few use cases. Here are some.

### Not hidden from press

* Active: publishing normally
* Archived: no longer publishing but have a backlist
* Coming soon: planning to start publishing soon
* Test: not applicable, as users should always hide test journals from the press

### Hidden from press

* Active: publishing normally but do not wish to be listed on the publisher site
* Archived: no longer published by the press but back content is still available at the journal site
* Coming soon: planning to start publishing soon but want to avoid appearing on the press site
* Test: testing options and training editors

## What areas are affected by these configuration options?

The `hide_from_press` field does exactly what it says--it puts up a wall between the journal and press, preventing records like `Journal`, like `Issue`, `Section`, `Article`, and `NewsItem` from showing up on press level websites and APIs.

The "Test" publishing status prevents users from accidentally sending data to places it is difficult to remove, like DOI registration. It does not interfere with anything else, including sitemaps, APIs, or RSS feeds, because these too are features that users would want to test at the journal level. This is why it is important for test journals to have `hide_from_press` turned on.

### User interfaces

| Area                                      | Hide from press   | Test status |
|-------------------------------------------|-------------------|-------------|
| Lists of journals on press website        | Does what it says | No effect   |
| Journal submission in repository system   | No effect         | Prevented   |
| Publications list on public user profiles | Does what it says | Not listed  |
| Back-office menus that list journals      | No effect         | No effect   |
| Django admin menus that list journals     | No effect         | No effect   |
| Reporting (plugin)                        | Does what it says | No effect   |

### Data feeds and alternate user interfaces

| Area                       | Hide from press   | Test status                       |
|----------------------------|-------------------|-----------------------------------|
| sitemaps                   | Does what it says | No effect                         |
| APIs                       | Does what it says | No effect                         |
| RSS/Atom feed              | Does what it says | No effect                         |
| reader notifications       | Not applicable    | No effect                         |
| Crossref deposits          | Not applicable    | Deposits use Crossref test server |
| Datacite deposits (plugin) | Not applicable    | Deposits use Datacite test server |
| Galley healthcheck command | Not applicable    | Articles ignored                  |
| DOI check command          | Not applicable    | Articles ignored                  |
| Store ithenticate command  | Not applicable    | Articles ignored                  |
| Metrics core app           | Does what it says | Articles excluded                 |
