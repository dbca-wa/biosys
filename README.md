# BioSys - Biological Survey Database System #

BioSys is a biological survey database system for Science and
Conservation Division within the Department of Parks and Wildlife.

Confluence URL:
[BioSys](https://confluence.dpaw.wa.gov.au/display/KM/BioSys+-+Biological+Survey+Database+System)

## Getting Started

Biosys is build on Django, the Python web framework and also requires a PostgreSQL database server
(9.3+) with the PostGIS extension.

It is recommended that the system is run in a Python virtual environment to allow the dependent
libraries to be installed without possible collisions with other versions of the same libraries.

## Requirements

### Supporting Applications / Packages:

- PostgreSQL (>=9.3)
- PostGIS extension (>=2.1)

### Python Libraries

Python library requirements should be installed using `pip`:

`pip install -r requirements.txt`

## Environment settings

The following environment settings should be defined in a `.env` file
(set at runtime by `django-confy`). Required settings:

    DJANGO_SETTINGS_MODULE="biosys.settings"
    DEBUG=True
    DATABASE_URL="postgres://USER:PASSWORD@HOST:PORT/NAME"
    SECRET_KEY="ThisIsASecretKey"
    CSRF_COOKIE_SECURE=False
    SESSION_COOKIE_SECURE=False
    KMI_USER="KMIUSER"
    KMI_PASSWORD="PASSWORD"
    KMI_WFS_URL="https://kmi.dpaw.wa.gov.au/geoserver/ows?service=wfs&version=1.0.0&request=GetCapabilities&typeNames={}&outputFormat=application/json"

## Running

Start the application on port 8080:

`python manage.py runserver 0.0.0.0:8080`

## Testing

To run unit tests or generate test coverage reports:

    python manage.py test -k -v2
    coverage run --source='.' manage.py test -k -v2
    coverage report -m
