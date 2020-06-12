![Janeway Logo](http://www.openlibhums.org/hosted_files/Janeway-Logo-05.png "Janeway")

Janeway is a journal platform designed for publishing scholarly research material. It is developed and maintained by the Centre for Technology and Publishing at Birkbeck, University of London.

# Technology
Janeway is written in Python (3.5+) and utilises the Django framework (1.11 LTS). 


# Installation instructions
Developer installation [instructions are available on our Wiki](https://github.com/BirkbeckCTP/janeway/wiki/Installation).

A guide for installing on the live environment with [apache and mod_wsgi](https://github.com/BirkbeckCTP/janeway/wiki/Janeway%2C-Apache-and-WSGI) is also available.

## Running Janeway with docker
Janeway's development server can be run within a docker container, avoiding the need to install and run its dependencies from your machine. A docker-compose file as well as a Makefile can be found at the root of the project wrapping the most common operations.
Docker is compatible with multiple architectures and Operating systems, if you need help installing docker, have a look at the [docker documentation](https://docs.docker.com/install/).

Simarly to the native installation, Janeway can be installed in a docker environment by running ``make install`` and following the installation steps described [above](https://github.com/BirkbeckCTP/janeway/wiki/Installation). As a result, a database volume will be populated under janeway/db/postgres-data
Once installation is completed, just type ``make`` to run janeway with a postgres backend (default behaviour).

If a change to the dependencies for Janeway is required, the Janeway container can be re-created with ``make rebuild``. The database volume will be preserved.

In order to run a different RDBMS, the environment variable ``DB_VENDOR`` can be set to one of ``postgres``, ``mysql`` or ``sqlite``. e.g: ``DB_VENDOR=mysql make install && make``

Uninstalling Janeway is as simple as running ``make uninstall`` which will delete all related containers as well as wipe the database volume.

# Using Lando for an alternative development environment (optional)

Lando provides a simple-to-use alternative to managing a development environment, while maintaining future flexibility to alter different aspects of the environment. Here are the steps required to get the app running on your local machine, with Lando
1. Make sure [Lando](https://lando.dev/) is installed
 > Lando comes bundled with Docker Desktop, if you already have Docker Desktop installed, don't re-install it, just ensure you have the same (or newer) version as what is bundled with Lando.
2. Copy `local.env.example` to `local.env` and customize as appropriate (the database configuration is done with environment variables, so pay attention to `local.env` if it's important to you--however, the `defaults.env` file should be sufficient to get started)
3. `lando poweroff` (defensively ensure no other Lando environments are running, probably not necessary, but a good habit)
4. `lando rebuild`
5. When you see the big "Boomshakala" message from Lando, you're ready to proceed
6. `lando django-admin check` will validate the installation is working
7. Revise your src/core/settings.py file as directed in the [Installation](https://janeway.readthedocs.io/en/feature-documentation/installation.html#database-setup-and-final-installation) instructions
8. `lando logs -f` will show you the log output from Django, though when you're getting started, `lando django-admin check` will help you find configuration errors much faster than sifting through log file output
9. `lando manage <command>` will send commands to the src/core/manage.py script, run `lando manage -h` to see more info
10. `lando manage install_janeway` will continue your installation of Janeway
11. `lando manage test` will run the Janeway unit test suite
11. `lando python <command>` will send Python commands to the appserver
12. Browse to `http://localhost:8000` to see the site in action
13. run `lando` to see what other Lando tooling commands are available.

# Lando Tooling
* `lando psql` Drops into the PostgreSQL client running on the database service
* `lando db-import <file>` Imports a dump file into the database service
* `lando ssh` Drops into a shell on the application service, runs commands
* `lando start` Starts the Janeway app
* `lando stop` Stops the Janeway app
* `lando rebuild` Rebuilds the Janeway app
* `lando restart` Simply starts and stops the Janeway app
* `lando destroy` Removes all traces of the Janeway dev environment's containers, useful if you need to ensure a fresh start

More Lando [tooling](https://docs.lando.dev/config/tooling.html) can be added easily.

# Janeway design principles
1. No code should appear to work "by magic". Readability is key.

2. Testing will be applied to security modules and whenever a post-launch bugfix is committed. We do not aim for total testing but selective regression testing.

3. Security bugs jump the development queue and are a priority.

4. We will never accept commits of, or ourselves write, paywall features into Janeway.

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
