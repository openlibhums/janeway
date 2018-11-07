ifndef POSTGRES_DB
	POSTGRES_HOST=janeway-postgres
	POSTGRES_PORT=5432
	POSTGRES_DB=janeway
	POSTGRES_USER=janeway-web
	POSTGRES_PASSWORD=janeway-web
endif

export POSTGRES_HOST
export POSTGRES_PORT
export POSTGRES_DB
export POSTGRES_USER
export POSTGRES_PASSWORD

all:
	docker-compose up
run-janeway:
	docker-compose run janeway-web
command:
	bash -c "docker-compose run janeway-web python3 src/manage.py $(CMD)"
install:
	bash -c "make command CMD=install_janeway"
rebuild:
	docker-compose build --no-cache

