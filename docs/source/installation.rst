Installation Guide
==================

Janeway includes an environment setup script that will install virtual
environment, its apt requirements and pip requirements. Please read the
script to ensure it wont cause any issues with your current install. The
command can be called directly from the command line:

Ubuntu:
``wget -O - https://raw.githubusercontent.com/BirkbeckCTP/janeway/master/setup_scripts/ubuntu.sh | bash``

Debian:
``wget -O - https://raw.githubusercontent.com/BirkbeckCTP/janeway/master/setup_scripts/debian.sh | bash``

This command has been tested in 14.04, 15.04 and 16.04

You should now proceed to “Database Setup and Final Installation”,
below.

Using Lando for a development environment (optional)
-----------------------------------------------------------------

`Lando <https://lando.dev/>`_ can be used to construct and manage a local a 
development environment. Here are the steps required to get Janeway running on 
your local machine, using Lando:

.. note:: Lando comes bundled with Docker Desktop, if you already have Docker 
  Desktop installed, don't re-install it. You should instead ensure you have the 
  same (or newer) version as what is bundled with Lando.

1. Make sure `Lando <https://lando.dev/>`_ is installed
2. Optionally, copy ``dockerfiles/lando_local.env.example`` to ``dockerfiles/lando_local.env`` and customize as appropriate (the
   database configuration is done with environment variables, so pay attention to 
   ``dockerfiles/lando_local.env`` if it's important to you)
3. ``lando poweroff`` (defensively ensure no other Lando environments are running, probably not necessary, but a good habit)
4. ``lando rebuild``
5. When you see the big "Boomshakala" message from Lando, you're ready to proceed
6. ``lando manage check`` will confirm the installation is working, and notify you of any misconfigurations
7. Revise your src/core/settings.py file as directed in the `Database Setup and Final Installation`_ instructions below
8. ``lando logs -f`` will show you the log output from Janeway, though when you're getting started, `lando manage check` will help you find configuration errors much faster than sifting through log file output
9. ``lando manage <command>`` will send commands to the src/core/manage.py script, run `lando manage -h` to see more info
10. ``lando manage install_janeway`` will continue your installation of Janeway
11. ``lando manage test`` will run the Janeway unit test suite
12. ``lando python <command>`` will send Python commands to the appserver
13. Browse to `http://localhost:8000` to see the site in action
14. run ``lando`` to see what other Lando tooling commands are available.

Lando Tooling
-------------

* ``lando psql`` Drops into the PostgreSQL client running on the database service
* ``lando db-import <file>`` Imports a dump file into the database service
* ``lando ssh`` Drops into a shell on the application service, runs commands
* ``lando start`` Starts the Janeway app
* ``lando stop`` Stops the Janeway app
* ``lando rebuild`` Rebuilds the Janeway app
* ``lando restart`` Starts and stops the Janeway app, useful for forcing the app to use new configurations
* ``lando destroy`` Removes all traces of the Janeway dev environment's containers, useful if you need to ensure a fresh start

More Lando `tooling <https://docs.lando.dev/config/tooling.html>`_ can be added, if you need it.

Manual Install
--------------

The following is for Debian/Ubuntu-based systems (16.04).

1. Install python3, pip3 & virtualevwrapper and create a project

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

   ``pip3 install -r requirements.txt``

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

   > Thanks! We will now set up out first journal.

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
