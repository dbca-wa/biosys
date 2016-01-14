# BioSys - Biological Survey Database System #

BioSys is a proposed biological survey database system for Science and
Conservation Division within the Department of Parks and Wildlife.

Confluence URL:
[BioSys](https://confluence.dpaw.wa.gov.au/display/KM/BioSys+-+Biological+Survey+Database+System)

## Getting Started

Biosys is build on Django, the Python web framework and also requires a PosgreSQL database server (9.3), with the PostGIS extension.

It is recommended that the system is run in a Python virtual environment to allow the dependent libraries to be installed without possible collisions with other versions of the same libraries.

## Requirements

### Supporting Applications / Packages:

- PostgreSQL (>=9.3)
- PostGIS extension (>=2.1)

### Python Libraries

Python library requirements should be installed using `pip`:

`pip install -r requirements.txt`

## Environment settings

The following environment settings should be defined in a `.env` file
(used by `honcho`, below). Example settings:

    DEBUG=True
    PORT=8080
    DATABASE_URL="postgres://USER:PASSWORD@HOST:PORT/NAME"
    SECRET_KEY="ThisIsASecretKey"
    LDAP_SERVER_URI="ldap://URL"
    LDAP_ACCESS_DN="ldap-access-dn"
    LDAP_ACCESS_PASSWORD="password"
    LDAP_SEARCH_SCOPE="DC=searchscope"

## Running

Use `honcho` to run a local copy of the application:

`honcho start`

## Testing

Use `honcho` to run unit tests or generate test coverage reports:

    honcho run python manage.py test -k -v2
    honcho run coverage run --source='.' manage.py test -k -v2
    honcho run coverage report -m
