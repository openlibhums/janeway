Installation Guide
==================

Janeway includes and environment setup script that will install virtual
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