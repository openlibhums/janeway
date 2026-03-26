Lando Development Setup
=======================

This guide describes a working local Janeway development setup using Lando.
It is intended for contributors who want a repeatable setup on macOS, Linux,
 or Windows without maintaining a separate native Python environment.

Why this guide exists
---------------------

Janeway can run in either path mode or domain mode. For the Lando setup in
this repository, the most reliable local configuration is:

* Janeway served at ``http://janeway.lndo.site/``
* Janeway development settings loaded from ``core.dev_settings``
* ``URL_CONFIG = "domain"`` in ``src/core/dev_settings.py``

Using path mode locally would require browsing to a URL like
``/Journal/``. The current Lando setup is intentionally configured for the
root-domain variant instead.

The local Lando appserver also uses a small wrapper script,
``dockerfiles/lando-runserver-loop.sh``, to keep the Django development server
available after ``lando restart-runserver`` or a transient local crash. This
script is only used by the Lando appserver command in ``.lando.yml`` and does
not affect non-Lando installs or production deployments.

Prerequisites
-------------

1. Install Docker Desktop or Docker Engine.
2. Install Lando: https://lando.dev/
3. Clone the Janeway repository.
4. Ensure port ``80`` is available on your machine for the Lando proxy.

Recommended versions
--------------------

The setup has been validated with these versions:

* Lando 3.25.x
* Docker Desktop 4.63.0 on macOS
* Docker Engine versions compatible with the above Lando release should also work on Linux

Other versions may also work, but if you hit unexpected startup or proxy
behaviour, first compare your local Lando and Docker versions with the tested
combination above.

What "multi-arch safe" means
----------------------------

Computers do not all use the same processor architecture. In local Docker
development, the two common ones are:

* ``amd64`` for most Intel and AMD machines
* ``arm64`` for Apple Silicon Macs and many ARM-based Linux machines

A multi-arch safe setup works on both without requiring contributors to keep
private overrides just to get through the initial build. The shared Janeway
Lando configuration installs ``lib32z1-dev`` only on ``amd64``-style
containers, because that package is not generally available on ``arm64``.

First-time setup
----------------

1. Clone the repository and enter the project directory.

   .. code-block:: bash

      git clone https://github.com/openlibhums/janeway.git
      cd janeway

2. Start or rebuild the Lando app.

   .. code-block:: bash

      lando rebuild -y

3. Run database migrations.

   .. code-block:: bash

      lando manage migrate

4. Run the Janeway installer.

   To run a non-interactive local install, use:

   .. code-block:: bash

      lando manage install_janeway --use-defaults

   In some environments, the installer defaults may save ``localhost`` as the
   Press domain and leave the first Journal domain blank. If that happens,
   align both with the Lando host:

   .. code-block:: bash

      lando manage shell -c "from press.models import Press; from journal.models import Journal; p=Press.objects.first(); j=Journal.objects.first(); p.domain='janeway.lndo.site'; p.save(); j.domain='janeway.lndo.site'; j.save()"

5. Create a superuser if you need access to Django admin features.

   .. code-block:: bash

      lando manage createsuperuser

6. Open Janeway:

   .. code-block:: text

      http://janeway.lndo.site/

   Use ``http`` for this local setup. ``https://janeway.lndo.site`` is not
   configured as the primary development URL here and may return a proxy-level
   error page.

Useful commands
---------------

Start or rebuild the environment:

.. code-block:: bash

   lando rebuild -y

Open a Django shell:

.. code-block:: bash

   lando manage shell

Run a management command:

.. code-block:: bash

   lando manage <command>

Restart only the Django development server:

.. code-block:: bash

   lando restart-runserver

This command intentionally stops the current ``runserver`` process and relies
on the Lando appserver wrapper script to bring it back automatically.

Inspect the active URLs:

.. code-block:: bash

   lando info

Expected local settings
-----------------------

The Lando setup in this repository expects the following local configuration:

* ``src/core/dev_settings.py``
* ``DEFAULT_HOST = "http://janeway.lndo.site"``
* ``URL_CONFIG = "domain"``

Why ``URL_CONFIG = "domain"`` is needed
---------------------------------------

It is required for this Lando setup.

The local proxy is configured so that Janeway is available at:

.. code-block:: text

   http://janeway.lndo.site/

In path mode, Janeway expects URLs like:

.. code-block:: text

   http://host/Journal/

That does not match the current Lando proxy design. Keeping local development
in domain mode avoids this mismatch and makes the local URL simpler.

Platform notes
--------------

macOS
~~~~~

On some macOS systems, ``*.lndo.site`` may not resolve correctly in the
browser. If ``http://janeway.lndo.site/`` does not resolve, add a hosts entry:

.. code-block:: text

   127.0.0.1 janeway.lndo.site

You will need administrator privileges to edit the hosts file.

The hosts file path on macOS is:

.. code-block:: text

   /etc/hosts

If you are on Apple Silicon and still hit a Docker image or package issue that
does not occur on Intel, you can add a temporary local override:

.. code-block:: yaml

   services:
     appserver:
       overrides:
         platform: linux/amd64

Save that as ``.lando.local.yml`` in the project root before running
``lando rebuild -y``. This file is intentionally local-only and should not be
committed.

Linux
~~~~~

If ``janeway.lndo.site`` does not resolve, add the same entry to:

.. code-block:: text

   /etc/hosts

using an account with permission to edit that file.

Windows
~~~~~~~

If ``janeway.lndo.site`` does not resolve, add the same entry to:

.. code-block:: text

   C:\Windows\System32\drivers\etc\hosts

You will need to edit the file with administrator privileges.

Troubleshooting
---------------

First boot after ``lando rebuild -y`` can be noisy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

On a fresh setup, the first boot can show transient startup errors while:

* Python dependencies are still finishing installation
* the database container is still becoming ready
* Django starts before migrations or initial Janeway data have been applied

This does not necessarily mean the setup is broken. A normal first-run
sequence is:

1. Run ``lando rebuild -y``.
2. Wait a few seconds after the rebuild completes.
3. Check whether the app is responding:

   .. code-block:: bash

      curl -I http://janeway.lndo.site/

4. If the appserver started but the database is not initialized yet, run:

   .. code-block:: bash

      lando manage migrate
      lando manage install_janeway --use-defaults

5. If Django started too early during the rebuild, restart only the runserver:

   .. code-block:: bash

      lando restart-runserver

During first boot, ``502 Bad Gateway``, ``ECONNRESET``, or database errors such
as ``relation "journal_journal" does not exist`` usually mean the services are
still settling or Janeway has not been installed yet, not that the Lando setup
itself is invalid.

If the installer has completed but the site still does not resolve correctly,
check whether the stored Press and Journal domains match the Lando host:

.. code-block:: bash

   lando manage shell -c "from press.models import Press; from journal.models import Journal; print('press=', Press.objects.first().domain); print('journal=', Journal.objects.first().domain)"

For this setup, both should resolve to:

.. code-block:: text

   janeway.lndo.site

``lando rebuild -y`` ends with ``502 Bad Gateway``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The proxy can be healthy before Django has fully restarted. Wait a few seconds,
then retry:

.. code-block:: bash

   curl -I http://janeway.lndo.site/

If needed, restart the development server:

.. code-block:: bash

   lando restart-runserver

The appserver command uses a small restart loop so that this command can stop
the current Django process without leaving the container permanently without a
development server.

``curl -I http://janeway.lndo.site/`` returns ``404 page not found``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check that local development is using domain mode:

* ``URL_CONFIG = "domain"``
* ``DEFAULT_HOST = "http://janeway.lndo.site"``

This setup is not intended to use ``/Journal/`` URLs locally.

``curl -I http://janeway.lndo.site/`` returns ``502 Bad Gateway``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Check whether Django is running:

.. code-block:: bash

   docker logs --tail 120 janeway_appserver_1

Then check whether the hostname resolves inside the app container:

.. code-block:: bash

   docker exec janeway_appserver_1 sh -lc "getent hosts db"

If the database host resolves but Django started too early, restarting the
development server is often enough:

.. code-block:: bash

   lando restart-runserver

If ``lando restart-runserver`` leaves the site unavailable, ensure your
checkout includes the Lando-only wrapper script at
``dockerfiles/lando-runserver-loop.sh`` and the corresponding ``command`` in
``.lando.yml``.

``https://janeway.lndo.site`` returns ``404`` or another proxy error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This setup is documented and tested against:

.. code-block:: text

   http://janeway.lndo.site/

If you open the same hostname over ``https``, the local proxy may return an
error page. Use the documented ``http`` URL unless you are explicitly testing
local HTTPS behaviour.

On Safari, a cached HSTS policy can also cause the browser to reopen the same
hostname over ``https`` even after you saved the ``http`` version as a
bookmark. If that happens, close the current tab first, then remove the stored
website data and reopen the ``http`` URL in a new tab or window:

1. Open ``Safari`` -> ``Settings``.
2. Go to ``Privacy``.
3. Click ``Manage Website Data...``.
4. Search for ``lndo.site``.
5. Remove the stored entry while the ``janeway.lndo.site`` tab is closed.
6. Open ``http://janeway.lndo.site/`` again in a new tab or window.

``janeway.lndo.site`` does not resolve
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add a hosts entry for your platform:

.. code-block:: text

   127.0.0.1 janeway.lndo.site

Why this should live in the open source repository
--------------------------------------------------

This guide belongs in the repository because it documents repository-specific
behaviour:

* the required ``env_file`` path
* the Lando proxy hostname
* the current local URL mode
* the platform-specific hostname workaround

Keeping it in versioned documentation makes it easier for contributors to
reproduce the setup and easier for maintainers to update the instructions when
the local development workflow changes.
