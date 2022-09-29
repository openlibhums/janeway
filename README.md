![Janeway Logo](http://www.openlibhums.org/hosted_files/Janeway-Logo-05.png "Janeway")

Janeway is a journal platform designed for publishing scholarly research material. It is developed and maintained by the Centre for Technology and Publishing at Birkbeck, University of London.

# Technology
Janeway is written in Python (3.6+) and utilises the Django framework (1.11 LTS). 


# Installation instructions
Developer installation [instructions are available in our documentation site](https://janeway.readthedocs.io/en/latest/installation.html#installation-guide).

A guide for installing on the live environment with [apache and mod_wsgi](https://github.com/BirkbeckCTP/janeway/wiki/Janeway%2C-Apache-and-WSGI) is also available.

## Running Janeway with docker
Janeway's development server can be run within a docker container, avoiding the need to install and run its dependencies from your machine. A docker-compose file as well as a Makefile can be found at the root of the project wrapping the most common operations.
Docker is compatible with multiple architectures and Operating systems, if you need help installing docker, have a look at the [docker documentation](https://docs.docker.com/install/).

Simarly to the native installation, Janeway can be installed in a docker environment by running ``make install`` and following the installation steps described [above](https://github.com/BirkbeckCTP/janeway/wiki/Installation). As a result, a database volume will be populated under janeway/db/postgres-data
Once installation is completed, just type ``make janeway`` to run janeway with a postgres backend (default behaviour).

If a change to the dependencies for Janeway is required, the Janeway container can be re-created with ``make rebuild``. The database volume will be preserved.

In order to run a different RDBMS, the environment variable ``DB_VENDOR`` can be set to one of ``postgres``, ``mysql`` or ``sqlite``. e.g: ``DB_VENDOR=mysql make install && make``

Uninstalling Janeway is as simple as running ``make uninstall`` which will delete all docker related containers as well as wipe the database volume.

# Janeway design principles
1. No code should appear to work "by magic". Readability is key.

2. Testing will be applied to security modules and whenever a post-launch bugfix is committed. We do not aim for total testing but selective regression testing.

3. Security bugs jump the development queue and are a priority.

4. We will never accept commits of, or ourselves write, paywall features into Janeway.

# Current development

What are we working on right now? For a high-level view, check out our [public roadmap on Trello](https://trello.com/b/Qnq2ySby/janeway-roadmap).

You can get more detail by viewing our [project boards here on GitHub](https://github.com/orgs/BirkbeckCTP/projects). Open a project to see which issues it includes and what their status is. The status should be one of these:

- To Do -- we plan to do this and include it in this release
- In Progress -- someone is working on it at this very moment!
- PR Submitted -- this means one developer has come up with a solution and is waiting for feedback from others
- Done -- this means at least one other developer has approved the solution and it has been merged into the main codebase in preparation for the release

We aim to build releases in 4-week sprints, though some development cycles have taken quite a bit longer.

# Licensing
Janeway is available under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE (Version 3, 19 November 2007).

# Contributions

We welcome all code contributions via Pull Requests where they can be reviewed and suggestions for enhancements via Issues. We do not currently have a  code of conduct for this repo but expect contributors to be courteous to one another.
In order to more easily associate changes to their respective github issues, please adhere to the following conventions:
 - Branch names should be prefixed with the issue number they are related to, followed by either "Feature" or "Hotfix" depending on the nature of the change ( e.g: `66-Feature`)
 - Start every commit with a reference to the github issue they are related to (e.g: `#66: Adds new feature xyz`)

# Contacts
If you wish to get in touch about Janeway, contact information is provided below.

Project Lead - Martin Paul Eve, martin.eve@bbk.ac.uk

Lead Developer - Andy Byers, a.byers@bbk.ac.uk

# Releases
- v1.0 Kathryn released 10/08/17
- v1.1 Chakotay released 01/09/17
- v1.2 Tuvok released 06/11/17
- v1.3 Doctor released 10/08/18

# Geolocation
Janeway includes GeoLite2 data created by MaxMind, available from [https://www.maxmind.com](https://www.maxmind.com)
