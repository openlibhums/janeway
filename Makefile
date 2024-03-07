ifndef DB_VENDOR
	DB_VENDOR=postgres
endif

# Exposed ports
JANEWAY_PORT ?= 8000
PGADMIN_PORT ?= 8001
SNAKEVIZ_PORT ?= 8002

unexport NO_DEPS
DB_NAME ?= janeway
DB_NAME ?= janeway
DB_HOST=janeway-postgres
DB_PORT=5432
DB_USER=janeway-web
DB_PASSWORD=janeway-web
DB_VOLUME=db/postgres-data
CLI_COMMAND=psql --username=$(DB_USER) $(DB_NAME)

ifeq ($(DB_VENDOR), mariadb)
	DB_HOST=janeway-mariadb
	DB_PORT=3306
	DB_USER=janeway-web
	DB_PASSWORD=janeway-web
	CLI_COMMAND=mysql -u $(DB_USER) -p$(DB_PASSWORD)
	DB_VOLUME=db/mariadb-data
endif

ifeq ($(DB_VENDOR), mysql)
	DB_HOST=janeway-mysql
	DB_PORT=3306
	DB_USER=janeway-web
	DB_PASSWORD=janeway-web
	CLI_COMMAND=mysql -u $(DB_USER) -p$(DB_PASSWORD)
	DB_VOLUME=db/mysql-data
endif

ifeq ($(DB_VENDOR), sqlite)
	unexport DB_HOST
	NO_DEPS=--no-deps
	CLI_COMMAND=sqlite db/janeway.sqlite3
	DB_VOLUME=db/janeway.sqlite3
endif

ifdef VERBOSE
	_VERBOSE=--verbose
endif

# Email
ifdef DEBUG_SMTP
	JANEWAY_EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
	JANEWAY_EMAIL_HOST=janeway-debug-smtp
	JANEWAY_EMAIL_PORT=1025
	JANEWAY_EMAIL_USE_TLS=
endif
LOCALES_DIR = ./src/core/locales

export DB_VENDOR
export DB_HOST
export DB_PORT
export DB_NAME
export DB_USER
export DB_PASSWORD
export JANEWAY_PORT
export PGADMIN_PORT

export JANEWAY_EMAIL_BACKEND
export JANEWAY_EMAIL_HOST
export JANEWAY_EMAIL_PORT
export JANEWAY_EMAIL_USE_TLS

SUFFIX ?= $(shell date +%s)
SUFFIX := ${SUFFIX}
DATE := `date +"%y-%m-%d"`

.PHONY: janeway
all: help
run: janeway
help:		## Show this help.
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'
janeway:	## Run Janeway web server in attached mode. If NO_DEPS is not set, runs all dependant services detached.
	docker-compose run --rm start_dependencies
	docker-compose $(_VERBOSE) run $(NO_DEPS) --rm --service-ports janeway-web $(entrypoint)
command:	## Run Janeway in a container and pass through a django command passed as the CMD environment variable (e.g make command CMD="migrate -v core 0024")
	docker-compose run $(NO_DEPS) --rm janeway-web $(CMD)
install:	## Run the install_janeway command inside a container
	touch db/janeway.sqlite3
	mkdir -p db/postgres-data
	docker-compose run --rm start_dependencies
	bash -c "make command CMD=install_janeway"
rebuild:	## Rebuild the Janeway docker image.
	docker pull birkbeckctp/janeway-base:latest
	docker-compose build --no-cache janeway-web
shell:		## Runs the janeway-web service and starts an interactive bash process instead of the webserver
	docker-compose run --service-ports --entrypoint=/bin/bash --rm janeway-web
attach:		## Runs an interactive shell within the currently running janeway-web container.
	docker exec -ti `docker ps -q --filter 'name=janeway-web'` /bin/bash
db-client:	## runs the database CLI client interactively within the database container as per the value of DB_VENDOR
	docker exec -ti `docker ps -q --filter 'name=janeway-$(DB_VENDOR)'` $(CLI_COMMAND)
db-save-backup: # Archives the current db as a tarball. Returns the output file name
	@sudo tar -zcf $(DB_VENDOR)-$(DATE)-$(SUFFIX).tar.gz $(DB_VOLUME)
	@echo "$(DB_VENDOR)-$(DATE)-$(SUFFIX).tar.gz"
	@sudo chown -R `id -un`:`id -gn` $(DB_VENDOR)-$(DATE)-$(SUFFIX).tar.gz
db-load-backup: #Loads a previosuly captured backup in the db directory (e.g.: make db-load_backup DB=postgres-21-02-03-3948681d1b6dc2.tar.gz)
	@BACKUP=$(BACKUP);echo "Loading $${BACKUP:?Please set to the name of the backup file}"
	@tar -zxf $(BACKUP) -C /tmp/
	@docker kill `docker ps -q --filter 'name=janeway-*'` 2>&1 | true
	@sudo rm -rf $(DB_VOLUME)
	@sudo mv /tmp/$(DB_VOLUME) db/
uninstall:	## Removes all janeway related docker containers, docker images and database volumes
	@bash -c "rm -rf db/*"
	@bash -c "docker rm -f `docker ps --filter 'name=janeway*' -aq` >/dev/null 2>&1 | true"
	@bash -c "docker rmi `docker images -q janeway*` >/dev/null 2>&1 | true"
	@echo " Janeway has been uninstalled"
check:		## Runs janeway's test suit
	bash -c "DB_VENDOR=sqlite make command CMD=test"
migrate:		## Runs Django's migrate command
	bash -c "make command CMD=migrate"
makemigrations:		## Runs Django's makemigrations command
	bash -c "make command CMD=makemigrations"
makemessages:
	#$(foreach file, $(wildcard $(LOCALES_DIR)/*), make command CMD="makemessages --locale=$(file) --ignore=src/plugins/*";)
	#@for f in $(shell ls ${LOCALES_DIR}); make command CMD='makemessages --locale=$${f} --ignore=src/plugins/*';)
	bash -c "make command CMD='makemessages \
		--locale=de \
		--locale=cy \
		--locale=fr \
		--locale=it \
		--locale=nl \
		--locale=en-us \
		--ignore=src/plugins/* \
	'"

build_assets:		## Runs Janeway's build_assets command
	bash -c "make command CMD=build_assets"
basebuild:		## Builds the base docker image
	bash -c "docker build --no-cache -t birkbeckctp/janeway-base:latest -f dockerfiles/Dockerfile.base ."
snakeviz:
	docker-compose run --publish $(SNAKEVIZ_PORT):$(SNAKEVIZ_PORT) $(NO_DEPS) --rm --entrypoint=snakeviz janeway-web $(FILE) --server -H 0.0.0.0 -p $(SNAKEVIZ_PORT)
