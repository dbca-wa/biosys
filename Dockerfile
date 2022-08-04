# Prepare the base environment.
FROM python:2.7.18-buster as builder_base
MAINTAINER asi@dbca.wa.gov.au
LABEL org.opencontainers.image.source https://github.com/dbca-wa/biosys

RUN apt-get update -y \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends wget git libmagic-dev gcc binutils gdal-bin libgdal-dev proj-bin tzdata \
  #&& rm -rf /var/lib/apt/lists/* \
  && pip install --upgrade pip

# Install Python libs.
FROM builder_base as python_libs
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Update the Django <1.11 bug in django/contrib/gis/geos/libgeos.py
# Reference: https://stackoverflow.com/questions/18643998/geodjango-geosexception-error
RUN sed -i -e "s/ver = geos_version().decode()/ver = geos_version().decode().split(' ')[0]/" /usr/local/lib/python2.7/site-packages/django/contrib/gis/geos/libgeos.py

# Install the project.
COPY manage.py gunicorn.ini ./
COPY biosys ./biosys
RUN python manage.py collectstatic --noinput

# Run the application as the www-data user.
USER www-data
EXPOSE 8080
CMD ["gunicorn", "biosys.wsgi", "--config", "gunicorn.ini"]
