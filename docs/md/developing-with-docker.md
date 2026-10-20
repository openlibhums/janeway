# Guide to developing Janeway with Docker

In this guide we assume you know the basics of Docker and docker compose.

1. Install `docker` and `GNU Make`.
2. From the /path/to/janeway directory run `make install`.
3. A docker environment will be provisioned, and shortly after the janeway install script will run. Follow the instructions on screen to complete the installation.
   If you are running Docker for Mac, you might run into issues with "wrong platform: for the dependencies container. You can add the `DOCKER_DEFAULT_PLATFORM=linux/amd64` to an .env file or you can modify the docker compose with that option for the dependencies container if you don't mind having uncommitted changes hanging around.
4. Once install is complete run ``make janeway`` to run the django development server against a Postgres backend.
   If you are running Docker for Mac, you might encounter a "No such file or directory" error thrown by the start_django command. This has to do with the bound volume mounting of MacOS host directories (case insensitive filepath) to linux (case sensitive) using the default Docker for Mac file sharing system VirtioFS. You can solve this issue by going into your Docker for Mac settings and selecting a different file sharing system under Virtual Machine Options. gRPC FUSE works great.
5. For Janeway browse `http://localhost:8000/`.
6. If using Postgres you can also browse `http://localhost:8001` for pgadmin. The default root password is `janeway-web`.

The Makefile provides a number of other targets for common tasks during development.

* `make db-client`: Will open a database shell that matches your configured `DB_VENDOR`. (e.g. running `make db-client` with the default options will run an interactive psql instance from the postgres container)
* `make command` allows you to run django management commands using the CMD variable (e.g `make command CMD=migrate journal` would be equivalent to running `python3 src/manage.py migrate journal` in a native install)
* `make check` will run Janeway's test suite with some predetermined configuration options to improve performance:
   - It runs against a sqlite backend
   - database migrations are skipped
* If you want to run the test suite against the database server then run it as a django management command with ``make command CMD=test``
* `make attach`: Attach to the running Janeway container and run an interactive shell (a Janeway development server must be running with ``make run`` for this to work)
* `make shell`: Start a janeway container and run an interactive shell. (It will bind port 8000 on your host so you cannot run this if a janeway server is running, in that case use `make attach` instead)
* `make rebuild`: Rebuilds the Janeway docker container. It should only be used when you make changes to the dependencies that need to be installed (e.g adding add new library to ``requirements.txt``)
* `make db-save-backup`: Save a backup of the database container. The command will return the name of the file in which the backup is stored. The backup is created by compressing the entire database container volume.
* `make db-load-backup BACKUP=<backup file>`: Load a previously generated backup. You must set the BACKUP variable to the filename returned by a previous run of `make db-save-backup`


The Makefile can be configured with a number of variables to change the way in which your development environment is run.

* If you want to run janeway against a different database vendor, you can use the `DB_VENDOR` variable. The following values are supported: `postgres` (default), `mysql` or `sqlite`
    * e.g. if you want to install the development environment for Janeway using a mysql container, you can run `make install DB_VENDOR=mysql` for the installation and `make run DB_VENDOR=mysql` to spin up the mysql container alongside the Janeway development server.
* By default, the database backend will come with a database named `janeway`. If you want to Janeway against a different database (e.g.: you have multiple local databases) you can set the DB_NAME variable (e.g.: `make install DB_NAME="janeway_staging"` or `make run DB_NAME=janeway_production`
* The `JANEWAY_PORT` variable allows you to change the port to which the Janeway development server will be bound to on your host (set this if port 8000 is already in use by another service on your host)

If you want to install custom python libraries for development, you can drop them into the dev_requirements.txt file and run `make rebuild`. Rebuilding the container takes some time, so it is also possible to install python libraries in development mode. When installed in this manner, the library is mounted as a volume into the janeway container when you first run `make rebuild` and  you will be able to make changes to the library without having to run `make rebuild`. In order to install a library in development mode, copy the code to `/path/to/janeway/lib/` and run `make rebuild` once.