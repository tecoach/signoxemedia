date_time = $(shell date --iso=seconds)

fixtures_dir = fixtures/$(date_time)

loaddata_command = python manage.py loaddata

dumpdata_command = python manage.py dumpdata
dumpdata_flags = --indent=2 --format=yaml

help:
	@echo "run              Run dev sever"
	@echo "load             Load fixtures"
	@echo "dbbackup         Backup database"
	@echo "remotedbbackup   Backup remote database"
	@echo "dbreset          Reset database"
	@echo "dump             Dump data in database as fixtures"
	@echo "migrations       Runs 'manage.py makemigrations' and adds the migrations to git"
	@echo "upgrade          Updates requirements files and installs updated requirements"
	@echo "dockertest       Tests the app inside a Docker container"

PORT = 4000
HOST = 0.0.0.0

run:
	@python manage.py runserver $(HOST):$(PORT) --verbosity 3

dump:
	mkdir $(fixtures_dir)
	if [ -a fixtures/devicemanager.yaml ] ; \
	then \
		mv fixtures/devicemanager.yaml $(fixtures_dir) ; \
	fi;
	if [ -a fixtures/mediamanager.yaml ] ; \
	then \
		mv fixtures/mediamanager.yaml $(fixtures_dir) ; \
	fi;
	if [ -a fixtures/feedmanager.yaml ] ; \
	then \
		mv fixtures/feedmanager.yaml $(fixtures_dir) ; \
	fi;
	$(dumpdata_command) devicemanager $(dumpdata_flags) -o fixtures/devicemanager.yaml
	$(dumpdata_command) mediamanager $(dumpdata_flags) -o fixtures/mediamanager.yaml
	$(dumpdata_command) feedmanager $(dumpdata_flags) -o fixtures/feedmanager.yaml


load:
	$(loaddata_command) fixtures/user_data.yaml
	@if [ -a fixtures/mediamanager.yaml ] ; \
	then \
		$(loaddata_command) fixtures/mediamanager.yaml ; \
	fi;
	@if [ -a fixtures/devicemanager.yaml ] ; \
	then \
		$(loaddata_command) fixtures/devicemanager.yaml ; \
	fi;
	@if [ -a fixtures/feedmanager.yaml ] ; \
	then \
		$(loaddata_command) fixtures/feedmanager.yaml ; \
	fi;

dbbackup:
	@if [ -a db.sqlite3 ] ; \
	then \
		cp db.sqlite3 ../backups/local/db.sqlite3.$(date_time) ; \
	else \
		echo "Not using Sqlite or database not initialised" ;\
	fi;

remotedbbackup:
	scp signoxe-linode:signoxe_server/signoxe-server/db.sqlite3 ../backups/remote/db.sqlite3.$(date_time)

.dbdel:
	rm db.sqlite3

migrations:
	python manage.py makemigrations
	git add */migrations/*.py

.migrate:
	python manage.py migrate

reset: dbbackupdb .dbdel .migrate load

upgrade:
	@echo "Updating requirements files"
	@pur -i -f -r requirements-dev.pip
	@echo "\nUpdating dependencies"
	@pip install -r requirements-dev.pip

dockertest:
	@docker build . -t signoxe-server-test -f Dockerfile.test
