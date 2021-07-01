# BioSys - Biological Survey Database System #

BioSys is a biological survey database system for Science and
Conservation Division within the Department of Parks and Wildlife.

GitHub:
[BioSys](https://github.com/parksandwildlife/biosys)

## Getting Started

Biosys is built on Django - the Python web framework - and also requires a PostgreSQL database server
(9.6+) with the PostGIS extension.

## Requirements

### Supporting Applications / Packages:

- Python 3.8
- PostgreSQL (>=9.6)
- PostGIS extension (>=2.1)
- GDAL (>=1.10)

#### Running PostgreSQL / PostGIS for development:

Setting up PostgreSQL with PostGIS extensions to run natively can be burdensome in a development environment, therefore
it is recommended to use Docker. Assuming Docker is running, the following command will create the PostgreSQL/PostGIS
container:

```
docker run --name biosys-postgis -e POSTGRES_DB=biosys -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d mdillon/postgis
```

Note: There is a docker-compose file in the base directory of the project - this is aimed towards running both the Django
application and database in docker, so should not be used if you intend to run Django natively (recommended during development).

#### GDAL on Windows

To run Biosys on Windows, you must install the osgeo4w desktop application. Download the 32 bit or 64 bit version depending on your version of Windows:

https://trac.osgeo.org/osgeo4w/

The installer may require specification of the particular packages to install, in which case, select gdal (binary) library. The installer will prompot for
installation of dependencies, although these will be selected for you, so ensure you accept these dependencies. 

Once installed, you must ensure the GDAL_LIBRARY_PATH and GEOS_LIBRARY_PATH are set as environment variables
(or .env file in project directory - see below).

This will be the path of the gdal and geos_c DLL files (.dll extension not required), something similar to: 

```
GDAL_LIBRARY_PATH='C:\Program Files\OSGeo4W64\bin\gdal301'

GEOS_LIBRARY_PATH='C:\Program Files\OSGeo4W64\bin\geos_c'
```

#### Conda
`conda create --name biosys python=3.8.8`
`conda activate biosys`
`conda install gdal=2.3.3`
`conda install pathlib=1.0.1`
`conda install pyqt=5.9.2`

### Python Libraries

Python library requirements should be installed using `pip`:

`pip install -r requirements.txt`

It is highly recommended that you use a Python virtual environment to host these libraries. Follow the below guide for
steps to setting up a virtual environment:

https://docs.python.org/3/library/venv.html

## Configuring and running the application

### Environment settings

Environment settings are defined in:

`biosys/settings.py`

Almost all settings have default values, which for development should be adequate. If you need to override default
settings, this is achieved through environment variables. You can either set these manually, or if you prefer, define
them in a `.env` file in the project base directory. Some commonly overridden settings during development include:

```
DEBUG=True
DATABASE_URL="postgis://USER:PASSWORD@HOST:PORT/NAME"
SECRET_KEY="ThisIsASecretKey"
CSRF_COOKIE_SECURE=False
SESSION_COOKIE_SECURE=False
```

### Preparing the database

Before the Biosys application will run, you must set up the database and create the required tables.

Assuming there is an instance of PostgreSQL server with the PostGIS extension available, create an empty database
(usually called *biosys* however this can be anything). This can be done through the psql command line client or via
a graphical tool such as PgAdmin. If you have PostgreSQL/PostGIS running in Docker, the database may already have been
created as part of the container definition. For more information, see the resources below:

https://www.postgresql.org/docs/10/sql-createdatabase.html
https://www.pgadmin.org/

Once an empty database is available, and ensuring that the DATABASE_URL setting is set correctly, run:

`python manage.py migrate`

### Running

To start the application:

`python manage.py runserver`

By default this will run on http://127.0.0.1:8000/

#### Creating a superuser account

In order to access Biosys, you need a user account. An administritive account will give complete access. To create, run

`python manage.py createsuperuser`

and follow the prompts.

### Testing

To run unit tests or generate test coverage reports:

    python manage.py test -k -v2
    coverage run --source='.' manage.py test -k -v2
    coverage report -m

## Using Biosys

The Biosys server was formerly entirely Django based, however now exists mainly as a REST API. For legacy purposes, there
is still some UI available, however it is recommended to run the biosys-web Angular client as the main graphical interface. 

https://github.com/gaiaresources/biosys-web

There is interactive documentation, known as Swagger, that is very useful for understanding the REST API - this is the best
way to get started and can be accessed at:

http://127.0.0.1:8000/api/explorer/

## Using Docker

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

## AWS Elastic Beanstalk deployment

This project is set for Elastic Beanstalk deployment through the `.elasticbeanstalk` dir with the `.ebextensions\*` environment configuration.
Note: the deployment is set tu use the 3.6 eb platform.  

You have to install the eb cli:  
`pip install awsebcli`  
Note: It is recommended to install the eb cli in a different virtual env than the project.

You have to have the right credentials set for you AWS account. (~/.aws/credentials)

Example of how to create an environment:

    # create a environment with a load balancer with 2 EC2 + a postgres RDS micro
    eb create --scale 2 -db -db.engine postgres -db.i db.t2.micro
    # same as above with no load balancer (single instance)
    eb create --single -db -db.engine postgres -db.i db.t2.micro
    # example of uat for slug (mksas). One instance but with load balancer
    eb create --scale 1 -db -db.engine postgres -db.i db.t2.micro --profile mksas
    
Check environment
    
    eb status
    
Deploy :
    
        example: deploy on OEH uat. This assume you have an oeh AWS credential profile. 
        eb deploy biosys-uat --profile oeh
 