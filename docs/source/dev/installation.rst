Installation Guide
==================
There are a number of ways to get Janeway up and running. For development we recommend you use Docker with Postgres as the DB_VENDOR.

Running Janeway with Docker and docker compose
----------------------------------------------
1. Install ``docker`` and ``GNU Make``.
2. From the /path/to/janeway directory run ``make install``.
3. A docker environment will be provisioned, and shortly after the janeway install script will run. Follow the instructions on screen to complete the installation.
4. Once install is complete run ``make run`` to run the django development server against a Postgres backend.
5. For Janeway browse ``http://localhost:8000``/.
6. If using Postgres (e you can also browse ``http://localhost:8001`` for pgadmin. The default root password is `janeway-web`

The Makefile provides a number of other targets for common tasks during development.

* ``make db-client``: Will open a database shell that matches your configured ``DB_VENDOR``. (e.g. running ``make db-client`` with the default options will run an interactive psql instance from the postgres container)
* ``make command`` allows you to run django management commands using the CMD variable (e.g ``make command CMD=migrate journal`` would be equivalent to running `python3 src/manage.py migrate journal` in a native install)
* ``make check`` will run Janeway's test suite with some predetermined configuration options to improve performance:
   * It runs against a sqlite backend
   * database migrations are skipped
* If you want to run the test suite against the database server then run it as a django management command with ``make command CMD=test``
* ``make attach``: Attach to the running Janeway container and run an interactive shell (a Janeway development server must be running with ``make run`` for this to work)
* ``make shell``: Start a janeway container and run an interactive shell. (It will bind port 8000 on your host so you cannot run this if a janeway server is running, in that case use `make attach` instead)
* ``make rebuild``: Rebuilds the Janeway docker container. It should only be used when you make changes to the dependencies that need to be installed (e.g adding add new library to ``requirements.txt``)
* ``make db-save-backup``: Save a backup of the database container. The command will return the name of the file in which the backup is stored. The backup is created by compressing the entire database container volume.
* ``make db-load-backup BACKUP=<backup file>``: Load a previously generated backup. You must set the BACKUP variable to the filename returned by a previous run of ``make db-save-backup``


The Makefile can be configured with a number of variables to change the way in which your development environment is run.

* If you want to run janeway against a different database vendor, you can use the `DB_VENDOR` variable. The following values are supported: ``postgres`` (default), ``mysql`` or ``sqlite``
    * e.g. if you want to install the development environment for Janeway using a mysql container, you can run ``make install DB_VENDOR=mysql`` for the installation and ``make run DB_VENDOR=mysql`` to spin up the mysql container alongside the Janeway development server.
* By default, the database backend will come with a database named ``janeway``. If you want to Janeway against a different database (e.g.: you have multiple local databases) you can set the DB_NAME variable (e.g.: ``make install DB_NAME="janeway_staging"`` or ``make run DB_NAME=janeway_production``
* The ``JANEWAY_PORT`` variable allows you to change the port to which the Janeway development server will be bound to on your host (set this if port 8000 is already in use by another service on your host)

If you want to install custom python libraries for development, you can drop them into the dev_requirements.txt file and run ``make rebuild``. Rebuilding the container takes some time, so it is also possible to install python libraries in development mode. When installed in this manner, the library is mounted as a volume into the janeway container when you first run `make rebuild` and  you will be able to make changes to the library without having to run ``make rebuild``. In order to install a library in development mode, copy the code to ``/path/to/janeway/lib/`` and run ``make rebuild`` once.


Native Install
--------------

The following is for Debian/Ubuntu-based systems (16.04).

1. Install python3, pip3 & virtualenvwrapper and create a project

::

   sudo apt-get install python3 python3-pip python-pip virtualenvwrapper
   source /etc/bash_completion.d/virtualenvwrapper
   mkvirtualenv janeway -p /usr/bin/python3

2. Install system dependencies.

On Ubuntu systems:
``sudo apt-get install libxml2-dev libxslt1-dev python3-dev zlib1g-dev lib32z1-dev libffi-dev libssl-dev libjpeg-dev libmysqlclient-dev``

On Debian systems:
``sudo apt-get install libxml2-dev libxslt1-dev python3-dev zlib1g-dev lib32z1-dev libffi-dev libssl-dev libjpeg-dev``

3. Clone the janeway repo to your local machine:
   ``git clone https://github.com/BirkbeckCTP/janeway.git``

4. From the project root directory run the following to install python
   dependencies:

   ``pip3 install -r requirements.txt -c constraints.txt``

You should now proceed to “Database Setup and Final Installation”,
below.

Database Setup and Final Installation
-------------------------------------

1. Copy the example settings file:
   ``cp src/core/example_settings.py src/core/settings.py``
2. Update settings.py for your env (database login etc.) and setup your
   database. This must support utf8_mb4. For MySQL installs, use the
   following CREATE command:

   ``CREATE DATABASE janeway CHARACTER SET = utf8 COLLATE = utf8_general_ci;``

3. From inside the src directory, switch to the virtual environment:

   ``workon janeway``

4. Run the installer

   ``python3 manage.py install_janeway``

and follow the on screen instructions.

::

   > Please answer the following questions.

   > Press name: Test Press

   > Press domain: test.press.com

   > Press main contact (email): ajrbyers@gmail.com

   > Thanks! We will now set up our first journal.

   > Journal #1 code: tstj

   > Journal #1 domain: journal.press.com

If you are installing Janeway on a live server rather than on your local
development environment its at this point you’ll need to look at a
webserver, Django is supported by Apache via mod_wsgi and with NGINX
through a variety of tools. We have an [[Apache and mod_wsgi (Server
Install)|Janeway,-Apache-and-WSGI]] guide.

4. Once the command line installer is complete you can complete the
   setup process by directing your browser to:
   http://yourfirstjournal.com/install/

Single Sign On
--------------
Janeway supports single sign on from two sources: Open ID Connect (OIDC) and ORCiD.

.. toctree::
   :maxdepth: 4
   :caption: SSO Providers

   oidc
   orcid
