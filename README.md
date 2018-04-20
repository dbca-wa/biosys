# BioSys - Biological Survey Database System #

BioSys is a biological survey database system for Science and
Conservation Division within the Department of Parks and Wildlife.

GitHub:
[BioSys](https://github.com/parksandwildlife/biosys)

## Getting Started

Biosys is built on Django, the Python web framework and also requires a PostgreSQL database server
(9.3+) with the PostGIS extension.

It is recommended that the system is run in a Python virtual environment to allow the dependent
libraries to be installed without possible collisions with other versions of the same libraries.

### Using Docker to take the app for a test-drive

**Note**: this Docker configuration is not production-ready. It is a super-quick way to get hands on with Biosys though.

Using [Docker](http://docker.com/) can help you get up and running quicker. To use this method, you'll need both [Docker](https://docs.docker.com/install/) and [docker-compose](https://docs.docker.com/compose/) installed.

First, we need to build the Docker image of the biosys app:
```bash
docker build -t dbca-wa/biosys .
```

Then we can start a stack that includes the app and a database:
```bash
docker-compose up
```

We need to wait ~15 seconds while the database schema is created and a superuser is created for us. Once that's done, you'll be able to access the UI at [http://localhost:8080/]() and login with username=`admin` and password=`admin`.

To clean up, you need to stop the running docker-compose stack using `<ctrl>+c`. Beware that the next step will **permanently delete** any data you created in the app. Then we can delete the stopped containers with:
```bash
docker-compose rm -f
```

**A note about postgres race condition**: Starting the docker-compose stack starts the database (postgres) and the app at the same time. Postgres needs to perform some startup steps before it's ready for a connection and we need the app to wait for this. At the moment it's done (badly) with a `sleep`. If you find that postgres starts slowly on your machine, edit the `docker-compose.yml` file and uncomment the `services.biosys.command` line and increase seconds if necessary.

## Requirements

### Supporting Applications / Packages:

- PostgreSQL (>=9.3)
- PostGIS extension (>=2.1)
- GDAL (>=1.10)

### Python Libraries

Python library requirements should be installed using `pip`:

`pip install -r requirements.txt`

## Environment settings

The following environment settings should be defined in a `.env` file
(set at runtime by `django-confy`). Required settings:

    DJANGO_SETTINGS_MODULE="biosys.settings"
    DEBUG=True
    DATABASE_URL="postgis://USER:PASSWORD@HOST:PORT/NAME"
    SECRET_KEY="ThisIsASecretKey"
    CSRF_COOKIE_SECURE=False
    SESSION_COOKIE_SECURE=False

## Running

Start the application on port 8080:

`python manage.py runserver 0.0.0.0:8080`

## Testing

To run unit tests or generate test coverage reports:

    python manage.py test -k -v2
    coverage run --source='.' manage.py test -k -v2
    coverage report -m
